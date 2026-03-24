from mail_rbl_monitor.domain.models import DnsblProvider
from mail_rbl_monitor.infrastructure.providers.catalog import (
    build_provider_query_context,
    get_provider_metadata,
)


def test_known_provider_metadata_has_expected_display_name() -> None:
    metadata = get_provider_metadata(DnsblProvider.from_raw("zen.spamhaus.org"))

    assert metadata.display_name == "Spamhaus ZEN"
    assert metadata.supports_txt is True
    assert metadata.supports_dqs is True
    assert metadata.dqs_zone_name == "zen"
    assert metadata.reference_url == "https://www.spamhaus.org/blocklists/zen-blocklist/"


def test_unknown_provider_metadata_is_safe() -> None:
    metadata = get_provider_metadata(DnsblProvider.from_raw("custom.example.org"))

    assert metadata.domain == "custom.example.org"
    assert metadata.display_name == "custom.example.org"
    assert metadata.supports_txt is True
    assert metadata.supports_dqs is False
    assert metadata.reference_url is None


def test_spamhaus_query_context_uses_public_mirror_without_dqs_key() -> None:
    context = build_provider_query_context(provider=DnsblProvider.from_raw("zen.spamhaus.org"))

    assert context.provider_mode.value == "public_mirror"
    assert context.query_zone == "zen.spamhaus.org"
    assert context.safe_query_zone == "zen.spamhaus.org"


def test_spamhaus_query_context_uses_redacted_dqs_zone_when_key_present() -> None:
    context = build_provider_query_context(
        provider=DnsblProvider.from_raw("zen.spamhaus.org"),
        spamhaus_dqs_key="test_dqs_key_1234567890abcdef123456",
    )

    assert context.provider_mode.value == "dqs"
    assert context.query_zone == "test_dqs_key_1234567890abcdef123456.zen.dq.spamhaus.net"
    assert context.safe_query_zone == "<spamhaus-dqs>.zen.dq.spamhaus.net"


def test_non_spamhaus_provider_query_context_remains_unchanged() -> None:
    context = build_provider_query_context(
        provider=DnsblProvider.from_raw("bl.spamcop.net"),
        spamhaus_dqs_key="test_dqs_key_1234567890abcdef123456",
    )

    assert context.provider_mode.value == "standard"
    assert context.query_zone == "bl.spamcop.net"
    assert context.safe_query_zone == "bl.spamcop.net"
