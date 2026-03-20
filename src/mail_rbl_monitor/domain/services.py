from datetime import UTC, datetime

from mail_rbl_monitor.domain.enums import AppEnvironment, NotificationChannel
from mail_rbl_monitor.domain.models import (
    AppRuntimeConfigSummary,
    DnsblProvider,
    OperatorAlertContext,
    RunSummary,
    TargetCheckResult,
    TargetIP,
)


def collect_enabled_channels(
    *, telegram_enabled: bool, discord_enabled: bool
) -> tuple[NotificationChannel, ...]:
    channels: list[NotificationChannel] = []

    if telegram_enabled:
        channels.append(NotificationChannel.TELEGRAM)
    if discord_enabled:
        channels.append(NotificationChannel.DISCORD)

    return tuple(channels)


def build_runtime_summary(
    *,
    environment: AppEnvironment,
    log_level: str,
    timeout_seconds: int,
    dry_run: bool,
    target_ips: tuple[TargetIP, ...],
    providers: tuple[DnsblProvider, ...],
    telegram_enabled: bool,
    discord_enabled: bool,
    alert_context: OperatorAlertContext,
) -> AppRuntimeConfigSummary:
    return AppRuntimeConfigSummary(
        environment=environment,
        log_level=log_level,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
        target_ips=target_ips,
        providers=providers,
        telegram_enabled=telegram_enabled,
        discord_enabled=discord_enabled,
        enabled_channels=collect_enabled_channels(
            telegram_enabled=telegram_enabled,
            discord_enabled=discord_enabled,
        ),
        alert_context=alert_context,
    )


def build_run_summary(
    *,
    runtime_config: AppRuntimeConfigSummary,
    checked_at_utc: str,
    target_results: tuple[TargetCheckResult, ...],
    host_label: str | None = None,
    notifications_sent: tuple[NotificationChannel, ...] = (),
    alert_message: str | None = None,
) -> RunSummary:
    return RunSummary(
        runtime_config=runtime_config,
        checked_at_utc=checked_at_utc,
        target_results=target_results,
        host_label=host_label,
        notifications_sent=notifications_sent,
        alert_message=alert_message,
    )


def format_utc_timestamp(value: datetime) -> str:
    normalized = value.astimezone(UTC).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def current_utc_timestamp() -> str:
    return format_utc_timestamp(datetime.now(UTC))
