from mail_rbl_monitor.application.formatters import format_listing_alert
from mail_rbl_monitor.domain.enums import (
    AppEnvironment,
    ListingStatus,
    NotificationChannel,
)
from mail_rbl_monitor.domain.models import (
    AppRuntimeConfigSummary,
    DnsblProvider,
    OperatorAlertContext,
    ProviderCheckResult,
    RunSummary,
    TargetCheckResult,
    TargetIP,
)


def _build_run_summary(
    *,
    include_hostname_in_alerts: bool,
    include_environment_in_alerts: bool,
    include_utc_timestamp_in_alerts: bool,
    host_label: str | None,
) -> RunSummary:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    return RunSummary(
        runtime_config=AppRuntimeConfigSummary(
            environment=AppEnvironment.PROD,
            log_level="INFO",
            timeout_seconds=5,
            dry_run=False,
            target_ips=(target_ip,),
            providers=(provider,),
            telegram_enabled=True,
            discord_enabled=False,
            enabled_channels=(NotificationChannel.TELEGRAM,),
            alert_context=OperatorAlertContext(
                host_label=host_label,
                include_hostname_in_alerts=include_hostname_in_alerts,
                include_environment_in_alerts=include_environment_in_alerts,
                include_utc_timestamp_in_alerts=include_utc_timestamp_in_alerts,
            ),
        ),
        checked_at_utc="2026-03-20T09:00:00Z",
        host_label=host_label,
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
                        txt_reasons=("Spamhaus listed",),
                    ),
                ),
            ),
        ),
    )


def test_format_listing_alert_includes_operator_context_when_enabled() -> None:
    run_summary = _build_run_summary(
        include_hostname_in_alerts=True,
        include_environment_in_alerts=True,
        include_utc_timestamp_in_alerts=True,
        host_label="mail-01",
    )

    message = format_listing_alert(run_summary)

    assert "[mail-rbl-monitor] LISTING DETECTED" in message
    assert "Environment: prod" in message
    assert "Host: mail-01" in message
    assert "Checked at (UTC): 2026-03-20T09:00:00Z" in message
    assert "Spamhaus ZEN (zen.spamhaus.org)" in message


def test_format_listing_alert_omits_optional_context_when_disabled() -> None:
    run_summary = _build_run_summary(
        include_hostname_in_alerts=False,
        include_environment_in_alerts=False,
        include_utc_timestamp_in_alerts=False,
        host_label="mail-01",
    )

    message = format_listing_alert(run_summary)

    assert "Environment: " not in message
    assert "Host: " not in message
    assert "Checked at (UTC): " not in message
    assert "Target IP: 136.243.71.222" in message
