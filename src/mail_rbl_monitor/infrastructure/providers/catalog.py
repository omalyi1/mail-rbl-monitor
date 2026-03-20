from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from mail_rbl_monitor.domain.models import DnsblProvider


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    domain: str
    display_name: str
    supports_txt: bool = True
    reference_url: str | None = None


_KNOWN_PROVIDERS: Final[dict[str, ProviderMetadata]] = {
    "zen.spamhaus.org": ProviderMetadata(
        domain="zen.spamhaus.org",
        display_name="Spamhaus ZEN",
        supports_txt=True,
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
