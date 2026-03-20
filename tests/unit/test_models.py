import pytest

from mail_rbl_monitor.domain.enums import AppEnvironment, ListingStatus
from mail_rbl_monitor.domain.exceptions import ConfigurationError
from mail_rbl_monitor.domain.models import (
    AppRuntimeConfigSummary,
    DnsblProvider,
    ProviderCheckResult,
    RunSummary,
    TargetCheckResult,
    TargetIP,
)


def test_target_ip_from_raw_accepts_ipv4_string() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")

    assert str(target_ip) == "136.243.71.222"


def test_dnsbl_provider_from_raw_normalizes_name() -> None:
    provider = DnsblProvider.from_raw("ZEN.SPAMHAUS.ORG")

    assert provider.name == "zen.spamhaus.org"


def test_dnsbl_provider_rejects_invalid_name() -> None:
    with pytest.raises(ConfigurationError, match="Invalid DNSBL provider name"):
        DnsblProvider.from_raw("not a provider")


def test_run_summary_reports_listing_and_error_counts() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    runtime_config = AppRuntimeConfigSummary(
        environment=AppEnvironment.TEST,
        log_level="INFO",
        timeout_seconds=5,
        dry_run=False,
        target_ips=(target_ip,),
        providers=(provider,),
        telegram_enabled=False,
        discord_enabled=False,
        enabled_channels=(),
    )
    run_summary = RunSummary(
        runtime_config=runtime_config,
        target_results=(
            TargetCheckResult(
                target_ip=target_ip,
                provider_results=(
                    ProviderCheckResult(
                        target_ip=target_ip,
                        provider=provider,
                        query_name="222.71.243.136.zen.spamhaus.org",
                        status=ListingStatus.LISTED,
                        listed_addresses=("127.0.0.2",),
                    ),
                    ProviderCheckResult(
                        target_ip=target_ip,
                        provider=provider,
                        query_name="222.71.243.136.zen.spamhaus.org",
                        status=ListingStatus.ERROR,
                        error_message="DNS query timed out.",
                    ),
                ),
            ),
        ),
    )

    assert run_summary.total_targets == 1
    assert run_summary.total_provider_checks == 2
    assert run_summary.listed_count == 1
    assert run_summary.error_count == 1
    assert run_summary.has_listings is True
    assert run_summary.has_errors is True
