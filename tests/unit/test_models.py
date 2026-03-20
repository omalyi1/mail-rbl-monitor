import pytest

from mail_rbl_monitor.domain.enums import (
    AppEnvironment,
    ListingStatus,
    NotificationChannel,
    ProviderErrorKind,
)
from mail_rbl_monitor.domain.exceptions import ConfigurationError, NotificationError
from mail_rbl_monitor.domain.models import (
    AppRuntimeConfigSummary,
    DnsblProvider,
    OperatorAlertContext,
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
        alert_context=OperatorAlertContext(
            host_label="mail-01",
            include_hostname_in_alerts=True,
            include_environment_in_alerts=True,
            include_utc_timestamp_in_alerts=True,
        ),
    )
    run_summary = RunSummary(
        runtime_config=runtime_config,
        checked_at_utc="2026-03-20T09:00:00Z",
        host_label="mail-01",
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
                        error_kind=ProviderErrorKind.TIMEOUT,
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
    assert run_summary.host_label == "mail-01"
    assert run_summary.checked_at_utc == "2026-03-20T09:00:00Z"


def test_notification_error_preserves_failure_accounting() -> None:
    error = NotificationError(
        "Discord notification delivery failed.",
        failed_channel=NotificationChannel.DISCORD,
        attempted_notification_channels=(
            NotificationChannel.TELEGRAM,
            NotificationChannel.DISCORD,
        ),
        notifications_sent_before_failure=(NotificationChannel.TELEGRAM,),
    )

    assert error.stage == "notification"
    assert error.failed_channel == NotificationChannel.DISCORD
    assert error.attempted_notification_channels == (
        NotificationChannel.TELEGRAM,
        NotificationChannel.DISCORD,
    )
    assert error.notifications_sent_before_failure == (NotificationChannel.TELEGRAM,)
