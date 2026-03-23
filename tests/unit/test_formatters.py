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
    TargetHost,
    TargetIP,
)


def _build_run_summary(
    *,
    include_hostname_in_alerts: bool,
    include_checked_at_in_alerts: bool,
    alert_timezone: str,
    target_hosts: tuple[TargetHost, ...] = (),
    checked_at_utc: str = "2026-03-23T10:12:02Z",
) -> RunSummary:
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    target_ip_primary = TargetIP.from_raw("136.243.71.222")
    target_ip_secondary = TargetIP.from_raw("136.243.71.219")
    return RunSummary(
        runtime_config=AppRuntimeConfigSummary(
            environment=AppEnvironment.PROD,
            log_level="INFO",
            timeout_seconds=5,
            dry_run=False,
            target_ips=(target_ip_primary, target_ip_secondary),
            providers=(provider,),
            telegram_enabled=True,
            discord_enabled=False,
            enabled_channels=(NotificationChannel.TELEGRAM,),
            alert_context=OperatorAlertContext(
                host_label="mail-01",
                include_hostname_in_alerts=include_hostname_in_alerts,
                include_checked_at_in_alerts=include_checked_at_in_alerts,
                alert_timezone=alert_timezone,
                target_hosts=target_hosts,
            ),
        ),
        checked_at_utc=checked_at_utc,
        host_label="mail-01",
        target_results=(
            TargetCheckResult(
                target_ip=target_ip_primary,
                provider_results=(
                    ProviderCheckResult(
                        target_ip=target_ip_primary,
                        provider=provider,
                        query_name="222.71.243.136.zen.spamhaus.org",
                        status=ListingStatus.LISTED,
                        listed_addresses=("127.0.0.2",),
                        txt_reasons=("Spamhaus listed",),
                    ),
                ),
            ),
            TargetCheckResult(
                target_ip=target_ip_secondary,
                provider_results=(
                    ProviderCheckResult(
                        target_ip=target_ip_secondary,
                        provider=provider,
                        query_name="219.71.243.136.zen.spamhaus.org",
                        status=ListingStatus.LISTED,
                        listed_addresses=("127.0.0.3",),
                    ),
                ),
            ),
        ),
    )


def test_format_listing_alert_includes_per_target_host_lines_when_configured() -> None:
    run_summary = _build_run_summary(
        include_hostname_in_alerts=True,
        include_checked_at_in_alerts=True,
        alert_timezone="Europe/Kyiv",
        target_hosts=(
            TargetHost(
                target_ip=TargetIP.from_raw("136.243.71.222"),
                hostname="mail.gol.ua",
            ),
            TargetHost(
                target_ip=TargetIP.from_raw("136.243.71.219"),
                hostname="mail.gol.lt",
            ),
        ),
    )

    message = format_listing_alert(run_summary)
    header_block = message.split("Target IP:", maxsplit=1)[0]

    assert "[mail-rbl-monitor] LISTING DETECTED" in message
    assert "Environment: " not in message
    assert "Host: " not in header_block
    assert "Checked at (Europe/Kyiv): 2026-03-23 12:12:02" in message
    assert "Target IP: 136.243.71.222\nHost: mail.gol.ua\nListed in:" in message
    assert "Target IP: 136.243.71.219\nHost: mail.gol.lt\nListed in:" in message
    assert "Spamhaus ZEN (zen.spamhaus.org)" in message


def test_format_listing_alert_omits_host_line_for_target_without_mapping() -> None:
    run_summary = _build_run_summary(
        include_hostname_in_alerts=True,
        include_checked_at_in_alerts=True,
        alert_timezone="Europe/Kyiv",
        target_hosts=(
            TargetHost(
                target_ip=TargetIP.from_raw("136.243.71.222"),
                hostname="mail.gol.ua",
            ),
        ),
    )

    message = format_listing_alert(run_summary)

    assert "Environment: " not in message
    assert "Checked at (Europe/Kyiv): 2026-03-23 12:12:02" in message
    assert "Target IP: 136.243.71.222\nHost: mail.gol.ua\nListed in:" in message
    assert "Target IP: 136.243.71.219\nListed in:" in message
    assert "Target IP: 136.243.71.219\nHost:" not in message
