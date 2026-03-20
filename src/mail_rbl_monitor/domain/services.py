from mail_rbl_monitor.domain.enums import AppEnvironment, NotificationChannel
from mail_rbl_monitor.domain.models import AppRuntimeConfigSummary, DnsblProvider, TargetIP


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
