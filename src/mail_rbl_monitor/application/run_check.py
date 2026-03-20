from __future__ import annotations

import logging

from mail_rbl_monitor.config import Settings
from mail_rbl_monitor.domain.models import AppRuntimeConfigSummary


def run_check(settings: Settings) -> AppRuntimeConfigSummary:
    summary = settings.to_runtime_summary()
    logger = logging.getLogger("mail_rbl_monitor.run_check")

    logger.info(
        "Loaded configuration successfully",
        extra={
            "event": "config.loaded",
            "app_env": summary.environment.value,
            "dry_run": summary.dry_run,
            "timeout_seconds": summary.timeout_seconds,
        },
    )
    logger.info(
        "Targets configured",
        extra={
            "event": "config.targets",
            "count": summary.target_count,
            "targets": [str(target_ip) for target_ip in summary.target_ips],
        },
    )
    logger.info(
        "Providers configured",
        extra={
            "event": "config.providers",
            "count": summary.provider_count,
            "providers": [str(provider) for provider in summary.providers],
        },
    )
    logger.info(
        "Notification channels configured",
        extra={
            "event": "config.notifications",
            "discord_enabled": summary.discord_enabled,
            "enabled_channels": [channel.value for channel in summary.enabled_channels],
            "telegram_enabled": summary.telegram_enabled,
        },
    )
    logger.info(
        "Dry run complete" if summary.dry_run else "Bootstrap complete",
        extra={"event": "run.complete", "dry_run": summary.dry_run},
    )

    return summary
