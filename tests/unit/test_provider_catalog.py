from mail_rbl_monitor.domain.models import DnsblProvider
from mail_rbl_monitor.infrastructure.providers.catalog import get_provider_metadata


def test_known_provider_metadata_has_expected_display_name() -> None:
    metadata = get_provider_metadata(DnsblProvider.from_raw("zen.spamhaus.org"))

    assert metadata.display_name == "Spamhaus ZEN"
    assert metadata.supports_txt is True
    assert metadata.reference_url == "https://www.spamhaus.org/blocklists/zen-blocklist/"


def test_unknown_provider_metadata_is_safe() -> None:
    metadata = get_provider_metadata(DnsblProvider.from_raw("custom.example.org"))

    assert metadata.domain == "custom.example.org"
    assert metadata.display_name == "custom.example.org"
    assert metadata.supports_txt is True
    assert metadata.reference_url is None
