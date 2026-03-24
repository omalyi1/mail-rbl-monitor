from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from mail_rbl_monitor.domain.enums import ProviderMode
from mail_rbl_monitor.domain.models import DnsblProvider

_SAFE_SPAMHAUS_DQS_LABEL: Final[str] = "<spamhaus-dqs>"
_SPAMHAUS_DQS_DOMAIN_SUFFIX: Final[str] = "dq.spamhaus.net"


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    domain: str
    display_name: str
    supports_txt: bool = True
    supports_dqs: bool = False
    dqs_zone_name: str | None = None
    reference_url: str | None = None


_KNOWN_PROVIDERS: Final[dict[str, ProviderMetadata]] = {
    "zen.spamhaus.org": ProviderMetadata(
        domain="zen.spamhaus.org",
        display_name="Spamhaus ZEN",
        supports_txt=True,
        supports_dqs=True,
        dqs_zone_name="zen",
        reference_url="https://www.spamhaus.org/blocklists/zen-blocklist/",
    ),
    "b.barracudacentral.org": ProviderMetadata(
        domain="b.barracudacentral.org",
        display_name="Barracuda Reputation Block List",
        supports_txt=True,
        reference_url="https://www.barracudacentral.org/rbl",
    ),
    "bl.spamcop.net": ProviderMetadata(
        domain="bl.spamcop.net",
        display_name="SpamCop Blocking List",
        supports_txt=True,
        reference_url="https://www.spamcop.net/bl.shtml",
    ),
}


@dataclass(frozen=True, slots=True)
class ProviderQueryContext:
    provider: DnsblProvider
    provider_mode: ProviderMode
    query_zone: str
    safe_query_zone: str
    display_name: str
    supports_txt: bool


def get_provider_metadata(provider: DnsblProvider) -> ProviderMetadata:
    return _KNOWN_PROVIDERS.get(
        provider.name,
        ProviderMetadata(
            domain=provider.name,
            display_name=provider.name,
            supports_txt=True,
            reference_url=None,
        ),
    )


def build_provider_query_context(
    *,
    provider: DnsblProvider,
    spamhaus_dqs_key: str | None = None,
) -> ProviderQueryContext:
    metadata = get_provider_metadata(provider)

    if (
        metadata.supports_dqs
        and metadata.dqs_zone_name is not None
        and spamhaus_dqs_key is not None
    ):
        normalized_key = spamhaus_dqs_key.strip()
        if normalized_key:
            actual_query_zone = (
                f"{normalized_key}.{metadata.dqs_zone_name}.{_SPAMHAUS_DQS_DOMAIN_SUFFIX}"
            )
            safe_query_zone = (
                f"{_SAFE_SPAMHAUS_DQS_LABEL}.{metadata.dqs_zone_name}.{_SPAMHAUS_DQS_DOMAIN_SUFFIX}"
            )
            return ProviderQueryContext(
                provider=provider,
                provider_mode=ProviderMode.DQS,
                query_zone=actual_query_zone,
                safe_query_zone=safe_query_zone,
                display_name=metadata.display_name,
                supports_txt=metadata.supports_txt,
            )

    provider_mode = (
        ProviderMode.PUBLIC_MIRROR if provider.name == "zen.spamhaus.org" else ProviderMode.STANDARD
    )
    return ProviderQueryContext(
        provider=provider,
        provider_mode=provider_mode,
        query_zone=metadata.domain,
        safe_query_zone=metadata.domain,
        display_name=metadata.display_name,
        supports_txt=metadata.supports_txt,
    )
