from __future__ import annotations

from dataclasses import dataclass

import dns.exception
import dns.resolver
import pytest

from mail_rbl_monitor.domain.enums import ListingStatus, ProviderErrorKind
from mail_rbl_monitor.domain.models import DnsblProvider, TargetIP
from mail_rbl_monitor.infrastructure.dns.resolver import DnsblResolver, build_dnsbl_query_name

type ResolverResponse = Exception | list[object]


@dataclass(frozen=True, slots=True)
class FakeARecord:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FakeTxtRecord:
    values: tuple[bytes, ...]

    @property
    def strings(self) -> tuple[bytes, ...]:
        return self.values


class FakeResolver:
    def __init__(self, responses: dict[tuple[str, str], ResolverResponse]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, str, int, bool]] = []

    def resolve(
        self,
        qname: str,
        rdtype: str,
        *,
        lifetime: int,
        search: bool,
    ) -> list[object]:
        self.calls.append((qname, rdtype, lifetime, search))
        response = self._responses[(qname, rdtype)]
        if isinstance(response, Exception):
            raise response
        return response


def _make_exception(exception_type: type[Exception]) -> Exception:
    return exception_type.__new__(exception_type)


def test_build_dnsbl_query_name_reverses_ipv4() -> None:
    query_name = build_dnsbl_query_name(
        TargetIP.from_raw("136.243.71.222").value, "zen.spamhaus.org"
    )

    assert query_name == "222.71.243.136.zen.spamhaus.org"


def test_resolver_classifies_nxdomain_as_clean() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    query_name = build_dnsbl_query_name(target_ip.value, provider.name)
    resolver = DnsblResolver(
        resolver=FakeResolver({(query_name, "A"): _make_exception(dns.resolver.NXDOMAIN)})
    )

    result = resolver.check_provider(target_ip, provider, timeout_seconds=5)

    assert result.status == ListingStatus.CLEAN
    assert result.query_name == query_name
    assert result.listed_addresses == ()
    assert result.txt_reasons == ()
    assert result.error_message is None
    assert result.error_kind is None


def test_resolver_classifies_a_answer_as_listed_and_reads_txt() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    query_name = build_dnsbl_query_name(target_ip.value, provider.name)
    resolver = DnsblResolver(
        resolver=FakeResolver(
            {
                (query_name, "A"): [FakeARecord("127.0.0.2"), FakeARecord("127.0.0.3")],
                (query_name, "TXT"): [
                    FakeTxtRecord((b"Spamhaus", b" listed")),
                    FakeTxtRecord((b"SBL",)),
                ],
            }
        )
    )

    result = resolver.check_provider(target_ip, provider, timeout_seconds=5)

    assert result.status == ListingStatus.LISTED
    assert result.listed_addresses == ("127.0.0.2", "127.0.0.3")
    assert result.txt_reasons == ("Spamhaus listed", "SBL")
    assert result.error_message is None
    assert result.error_kind is None


@pytest.mark.parametrize(
    ("listed_address", "expected_error_kind"),
    (
        ("127.255.255.252", ProviderErrorKind.DNS_EXCEPTION),
        ("127.255.255.254", ProviderErrorKind.OPEN_RESOLVER),
        ("127.255.255.255", ProviderErrorKind.DNS_EXCEPTION),
    ),
)
def test_resolver_classifies_spamhaus_special_return_codes_as_provider_errors(
    listed_address: str,
    expected_error_kind: ProviderErrorKind,
) -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    query_name = build_dnsbl_query_name(target_ip.value, provider.name)
    resolver = DnsblResolver(
        resolver=FakeResolver(
            {
                (query_name, "A"): [FakeARecord(listed_address)],
                (query_name, "TXT"): [FakeTxtRecord((b"Error: open resolver",))],
            }
        )
    )

    result = resolver.check_provider(target_ip, provider, timeout_seconds=5)

    assert result.status == ListingStatus.ERROR
    assert result.listed_addresses == (listed_address,)
    assert result.txt_reasons == ("Error: open resolver",)
    assert result.error_kind == expected_error_kind
    assert result.error_message is not None


def test_resolver_classifies_timeout_as_provider_error() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    query_name = build_dnsbl_query_name(target_ip.value, provider.name)
    resolver = DnsblResolver(
        resolver=FakeResolver({(query_name, "A"): _make_exception(dns.exception.Timeout)})
    )

    result = resolver.check_provider(target_ip, provider, timeout_seconds=5)

    assert result.status == ListingStatus.ERROR
    assert result.listed_addresses == ()
    assert result.txt_reasons == ()
    assert result.error_message == "DNS query timed out."
    assert result.error_kind == ProviderErrorKind.TIMEOUT


def test_resolver_classifies_no_answer_as_provider_error() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    query_name = build_dnsbl_query_name(target_ip.value, provider.name)
    resolver = DnsblResolver(
        resolver=FakeResolver({(query_name, "A"): _make_exception(dns.resolver.NoAnswer)})
    )

    result = resolver.check_provider(target_ip, provider, timeout_seconds=5)

    assert result.status == ListingStatus.ERROR
    assert result.error_kind == ProviderErrorKind.NO_ANSWER
    assert (
        result.error_message == "Provider returned no A answer; clean results must return NXDOMAIN."
    )


def test_resolver_classifies_no_nameservers_as_provider_error() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    query_name = build_dnsbl_query_name(target_ip.value, provider.name)
    resolver = DnsblResolver(
        resolver=FakeResolver({(query_name, "A"): _make_exception(dns.resolver.NoNameservers)})
    )

    result = resolver.check_provider(target_ip, provider, timeout_seconds=5)

    assert result.status == ListingStatus.ERROR
    assert result.error_kind == ProviderErrorKind.NO_NAMESERVERS
    assert result.error_message == "No nameserver could answer the DNS query."


def test_resolver_classifies_unexpected_exception_as_provider_error() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    query_name = build_dnsbl_query_name(target_ip.value, provider.name)
    resolver = DnsblResolver(resolver=FakeResolver({(query_name, "A"): RuntimeError("boom")}))

    result = resolver.check_provider(target_ip, provider, timeout_seconds=5)

    assert result.status == ListingStatus.ERROR
    assert result.error_kind == ProviderErrorKind.UNEXPECTED
    assert result.error_message == "Unexpected DNS resolution failure."
