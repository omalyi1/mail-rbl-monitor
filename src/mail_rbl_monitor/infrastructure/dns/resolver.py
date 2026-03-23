from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from ipaddress import IPv4Address
from typing import Protocol

import dns.exception
import dns.resolver

from mail_rbl_monitor.domain.enums import ListingStatus, ProviderErrorKind
from mail_rbl_monitor.domain.exceptions import ProviderResolutionError
from mail_rbl_monitor.domain.models import DnsblProvider, ProviderCheckResult, TargetIP
from mail_rbl_monitor.domain.ports import DnsResolverPort
from mail_rbl_monitor.infrastructure.providers.catalog import get_provider_metadata

_SPAMHAUS_SPECIAL_RETURN_CODES: dict[str, tuple[ProviderErrorKind, str]] = {
    "127.255.255.252": (
        ProviderErrorKind.DNS_EXCEPTION,
        "Spamhaus special return code 127.255.255.252 indicates a provider-side error.",
    ),
    "127.255.255.254": (
        ProviderErrorKind.OPEN_RESOLVER,
        "Spamhaus special return code 127.255.255.254 indicates an open resolver.",
    ),
    "127.255.255.255": (
        ProviderErrorKind.DNS_EXCEPTION,
        "Spamhaus special return code 127.255.255.255 indicates a provider-side error.",
    ),
}


class ResolverBackend(Protocol):
    def resolve(
        self,
        qname: str,
        rdtype: str,
        *,
        lifetime: int,
        search: bool,
    ) -> Iterable[object]: ...


def build_dnsbl_query_name(ip: IPv4Address, provider_domain: str) -> str:
    normalized_provider = provider_domain.strip().lower().rstrip(".")
    reversed_ip = ".".join(reversed(str(ip).split(".")))
    return f"{reversed_ip}.{normalized_provider}"


def _deduplicate_preserving_order(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _normalize_txt_record(record: object) -> str:
    strings = getattr(record, "strings", None)
    if isinstance(strings, tuple):
        normalized_parts = []
        for part in strings:
            if isinstance(part, bytes):
                normalized_parts.append(part.decode("utf-8", errors="replace"))
            else:
                normalized_parts.append(str(part))
        return "".join(normalized_parts)

    return str(record).replace('"', "").strip()


@dataclass(slots=True)
class DnsblResolver(DnsResolverPort):
    resolver: ResolverBackend = field(default_factory=dns.resolver.Resolver)

    def check_provider(
        self, target_ip: TargetIP, provider: DnsblProvider, timeout_seconds: int
    ) -> ProviderCheckResult:
        query_name = build_dnsbl_query_name(target_ip.value, provider.name)
        started_at = time.perf_counter()

        try:
            listed_addresses = self._resolve_a(
                query_name=query_name, timeout_seconds=timeout_seconds
            )
        except dns.resolver.NXDOMAIN:
            return ProviderCheckResult(
                target_ip=target_ip,
                provider=provider,
                query_name=query_name,
                status=ListingStatus.CLEAN,
                latency_ms=self._calculate_latency_ms(started_at),
            )
        except ProviderResolutionError as exc:
            return ProviderCheckResult(
                target_ip=target_ip,
                provider=provider,
                query_name=query_name,
                status=ListingStatus.ERROR,
                error_message=str(exc),
                error_kind=exc.error_kind,
                latency_ms=self._calculate_latency_ms(started_at),
            )

        txt_reasons: tuple[str, ...] = ()
        provider_metadata = get_provider_metadata(provider)
        if provider_metadata.supports_txt:
            txt_reasons = self._resolve_txt_best_effort(
                query_name=query_name,
                timeout_seconds=timeout_seconds,
            )

        spamhaus_error = _classify_spamhaus_special_return_code(
            provider=provider,
            listed_addresses=listed_addresses,
        )
        if spamhaus_error is not None:
            error_kind, error_message = spamhaus_error
            return ProviderCheckResult(
                target_ip=target_ip,
                provider=provider,
                query_name=query_name,
                status=ListingStatus.ERROR,
                listed_addresses=listed_addresses,
                txt_reasons=txt_reasons,
                error_message=error_message,
                error_kind=error_kind,
                latency_ms=self._calculate_latency_ms(started_at),
            )

        return ProviderCheckResult(
            target_ip=target_ip,
            provider=provider,
            query_name=query_name,
            status=ListingStatus.LISTED,
            listed_addresses=listed_addresses,
            txt_reasons=txt_reasons,
            latency_ms=self._calculate_latency_ms(started_at),
        )

    def _resolve_a(self, *, query_name: str, timeout_seconds: int) -> tuple[str, ...]:
        try:
            answer = self.resolver.resolve(
                query_name,
                "A",
                lifetime=timeout_seconds,
                search=False,
            )
        except dns.resolver.NXDOMAIN:
            raise
        except dns.resolver.NoAnswer as exc:
            raise ProviderResolutionError(
                "Provider returned no A answer; clean results must return NXDOMAIN.",
                error_kind=ProviderErrorKind.NO_ANSWER,
            ) from exc
        except dns.exception.Timeout as exc:
            raise ProviderResolutionError(
                "DNS query timed out.",
                error_kind=ProviderErrorKind.TIMEOUT,
            ) from exc
        except dns.resolver.NoNameservers as exc:
            raise ProviderResolutionError(
                "No nameserver could answer the DNS query.",
                error_kind=ProviderErrorKind.NO_NAMESERVERS,
            ) from exc
        except dns.exception.DNSException as exc:
            raise ProviderResolutionError(
                f"DNS query failed with {exc.__class__.__name__}.",
                error_kind=ProviderErrorKind.DNS_EXCEPTION,
            ) from exc
        except Exception as exc:
            raise ProviderResolutionError(
                "Unexpected DNS resolution failure.",
                error_kind=ProviderErrorKind.UNEXPECTED,
            ) from exc

        return _deduplicate_preserving_order(
            tuple(str(record) for record in answer if str(record).strip())
        )

    def _resolve_txt_best_effort(self, *, query_name: str, timeout_seconds: int) -> tuple[str, ...]:
        try:
            answer = self.resolver.resolve(
                query_name,
                "TXT",
                lifetime=timeout_seconds,
                search=False,
            )
        except (
            dns.exception.DNSException,
            dns.resolver.NoAnswer,
        ):
            return ()

        return _deduplicate_preserving_order(
            tuple(
                normalized_record
                for normalized_record in (_normalize_txt_record(record) for record in answer)
                if normalized_record
            )
        )

    @staticmethod
    def _calculate_latency_ms(started_at: float) -> int:
        return max(0, int((time.perf_counter() - started_at) * 1000))


def _classify_spamhaus_special_return_code(
    *,
    provider: DnsblProvider,
    listed_addresses: tuple[str, ...],
) -> tuple[ProviderErrorKind, str] | None:
    if provider.name != "zen.spamhaus.org":
        return None

    for listed_address in listed_addresses:
        special_return_code = _SPAMHAUS_SPECIAL_RETURN_CODES.get(listed_address)
        if special_return_code is not None:
            return special_return_code

    return None
