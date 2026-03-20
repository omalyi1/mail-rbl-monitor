from mail_rbl_monitor.domain.enums import AppEnvironment, NotificationChannel
from mail_rbl_monitor.domain.models import (
    AppRuntimeConfigSummary,
    DnsblProvider,
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
    )


def build_run_summary(
    *,
    runtime_config: AppRuntimeConfigSummary,
    target_results: tuple[TargetCheckResult, ...],
    notifications_sent: tuple[NotificationChannel, ...] = (),
    alert_message: str | None = None,
) -> RunSummary:
    return RunSummary(
        runtime_config=runtime_config,
        target_results=target_results,
        notifications_sent=notifications_sent,
        alert_message=alert_message,
    )
