from __future__ import annotations

import logging
import socket
from collections.abc import Sequence

from mail_rbl_monitor.application.formatters import format_listing_alert
from mail_rbl_monitor.config import Settings
from mail_rbl_monitor.domain.enums import NotificationChannel
from mail_rbl_monitor.domain.exceptions import NotificationError
from mail_rbl_monitor.domain.models import (
    AppRuntimeConfigSummary,
    ProviderCheckResult,
    RunSummary,
    TargetCheckResult,
    TargetIP,
)
from mail_rbl_monitor.domain.ports import DnsResolverPort, NotificationSenderPort
from mail_rbl_monitor.domain.services import build_run_summary, current_utc_timestamp
from mail_rbl_monitor.infrastructure.dns.resolver import DnsblResolver
from mail_rbl_monitor.infrastructure.notifications.discord import DiscordNotificationSender
from mail_rbl_monitor.infrastructure.notifications.telegram import TelegramNotificationSender
from mail_rbl_monitor.presentation.redaction import sanitize_operator_error_message


def run_check(
    settings: Settings,
    *,
    dns_resolver: DnsResolverPort | None = None,
    notification_senders: Sequence[NotificationSenderPort] | None = None,
) -> RunSummary:
    summary = settings.to_runtime_summary()
    checked_at_utc = current_utc_timestamp()
    host_label = _resolve_host_label(summary)
    logger = logging.getLogger("mail_rbl_monitor.run_check")

    _log_startup(
        summary=summary, checked_at_utc=checked_at_utc, host_label=host_label, logger=logger
    )

    if summary.dry_run:
        logger.info(
            "Dry run complete",
            extra={"event": "run.complete", "checked_at_utc": checked_at_utc, "dry_run": True},
        )
        return build_run_summary(
            runtime_config=summary,
            checked_at_utc=checked_at_utc,
            target_results=(),
            host_label=host_label,
        )

    resolver = dns_resolver or DnsblResolver(
        spamhaus_dqs_key=(
            settings.spamhaus_dqs_key.get_secret_value()
            if settings.spamhaus_dqs_key is not None
            else None
        )
    )
    target_results = tuple(
        _check_target(target_ip=target_ip, summary=summary, resolver=resolver, logger=logger)
        for target_ip in summary.target_ips
    )
    run_summary = build_run_summary(
        runtime_config=summary,
        checked_at_utc=checked_at_utc,
        target_results=target_results,
        host_label=host_label,
    )

    if run_summary.has_listings:
        alert_message = format_listing_alert(run_summary)
        senders = (
            tuple(notification_senders)
            if notification_senders is not None
            else _build_notification_senders(settings)
        )
        notifications_sent = _send_notifications(
            message=alert_message,
            senders=senders,
            logger=logger,
            secret_values=settings.operator_secret_values(),
        )
        run_summary = build_run_summary(
            runtime_config=summary,
            checked_at_utc=checked_at_utc,
            target_results=target_results,
            host_label=host_label,
            notifications_sent=notifications_sent,
            alert_message=alert_message,
        )
    elif run_summary.has_errors:
        logger.warning(
            "Provider errors detected with no listings",
            extra={
                "event": "run.provider_errors",
                "error_count": run_summary.error_count,
                "listed_count": run_summary.listed_count,
            },
        )

    logger.info(
        "Run complete",
        extra={
            "event": "run.complete",
            "dry_run": False,
            "error_count": run_summary.error_count,
            "listed_count": run_summary.listed_count,
            "notifications_sent": [channel.value for channel in run_summary.notifications_sent],
            "provider_checks": run_summary.total_provider_checks,
            "checked_at_utc": checked_at_utc,
            "host_label": host_label,
        },
    )

    return run_summary


def _log_startup(
    *,
    summary: AppRuntimeConfigSummary,
    checked_at_utc: str,
    host_label: str | None,
    logger: logging.Logger,
) -> None:
    logger.info(
        "Loaded configuration successfully",
        extra={
            "event": "config.loaded",
            "app_env": summary.environment.value,
            "checked_at_utc": checked_at_utc,
            "dry_run": summary.dry_run,
            "host_label": host_label,
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


def _check_target(
    *,
    target_ip: TargetIP,
    summary: AppRuntimeConfigSummary,
    resolver: DnsResolverPort,
    logger: logging.Logger,
) -> TargetCheckResult:
    provider_results = tuple(
        resolver.check_provider(target_ip, provider, summary.timeout_seconds)
        for provider in summary.providers
    )

    for provider_result in provider_results:
        _log_provider_result(provider_result=provider_result, logger=logger)

    return TargetCheckResult(target_ip=target_ip, provider_results=provider_results)


def _log_provider_result(*, provider_result: ProviderCheckResult, logger: logging.Logger) -> None:
    log_extra = {
        "event": "check.provider",
        "latency_ms": provider_result.latency_ms,
        "provider": provider_result.provider.name,
        "provider_mode": provider_result.provider_mode.value
        if provider_result.provider_mode is not None
        else None,
        "query_name": provider_result.query_name,
        "status": provider_result.status.value,
        "target_ip": str(provider_result.target_ip),
    }

    if provider_result.is_listed:
        logger.warning(
            "DNSBL listing detected",
            extra={
                **log_extra,
                "listed_addresses": list(provider_result.listed_addresses),
                "txt_reasons": list(provider_result.txt_reasons),
            },
        )
        return

    if provider_result.is_error:
        logger.warning(
            "DNSBL provider check failed",
            extra={
                **log_extra,
                "error_kind": provider_result.error_kind.value
                if provider_result.error_kind is not None
                else None,
                "error": provider_result.error_message,
            },
        )
        return

    logger.info("Target clean for provider", extra=log_extra)


def _build_notification_senders(settings: Settings) -> tuple[NotificationSenderPort, ...]:
    senders: list[NotificationSenderPort] = []

    if settings.enable_telegram:
        assert settings.telegram_bot_token is not None
        assert settings.telegram_chat_id is not None
        senders.append(
            TelegramNotificationSender(
                bot_token=settings.telegram_bot_token.get_secret_value(),
                chat_id=settings.telegram_chat_id,
                timeout_seconds=settings.timeout_seconds,
            )
        )

    if settings.enable_discord:
        assert settings.discord_webhook_url is not None
        senders.append(
            DiscordNotificationSender(
                webhook_url=settings.discord_webhook_url.get_secret_value(),
                timeout_seconds=settings.timeout_seconds,
            )
        )

    return tuple(senders)


def _send_notifications(
    *,
    message: str,
    senders: Sequence[NotificationSenderPort],
    logger: logging.Logger,
    secret_values: Sequence[str],
) -> tuple[NotificationChannel, ...]:
    notifications_sent: list[NotificationChannel] = []
    attempted_channels = tuple(sender.channel for sender in senders)

    if not senders:
        logger.warning(
            "Listing detected but no notification channels are enabled",
            extra={"event": "notification.skipped"},
        )
        return ()

    for sender in senders:
        try:
            sender.send(message)
        except NotificationError as exc:
            enriched_error = NotificationError(
                sanitize_operator_error_message(
                    str(exc),
                    secret_values=secret_values,
                    fallback=_notification_failure_message(sender.channel),
                ),
                stage=exc.stage,
                failed_channel=exc.failed_channel or sender.channel,
                attempted_notification_channels=(
                    exc.attempted_notification_channels or attempted_channels
                ),
                notifications_sent_before_failure=(
                    exc.notifications_sent_before_failure or tuple(notifications_sent)
                ),
            )
            _log_notification_failure(error=enriched_error, logger=logger)
            raise enriched_error from exc
        except Exception as exc:
            enriched_error = NotificationError(
                _notification_failure_message(sender.channel),
                failed_channel=sender.channel,
                attempted_notification_channels=attempted_channels,
                notifications_sent_before_failure=tuple(notifications_sent),
            )
            _log_notification_failure(error=enriched_error, logger=logger)
            raise enriched_error from exc

        notifications_sent.append(sender.channel)
        logger.info(
            "Alert notification sent",
            extra={
                "event": "notification.sent",
                "channel": sender.channel.value,
            },
        )

    return tuple(notifications_sent)


def _log_notification_failure(*, error: NotificationError, logger: logging.Logger) -> None:
    logger.error(
        "Alert notification failed",
        extra={
            "event": "notification.failed",
            "attempted_notification_channels": [
                channel.value for channel in error.attempted_notification_channels
            ],
            "failed_channel": error.failed_channel.value if error.failed_channel else None,
            "notifications_sent_before_failure": [
                channel.value for channel in error.notifications_sent_before_failure
            ],
            "stage": error.stage,
            "error": str(error),
        },
    )


def _notification_failure_message(channel: NotificationChannel) -> str:
    return f"{channel.value.capitalize()} notification delivery failed."


def _resolve_host_label(summary: AppRuntimeConfigSummary) -> str | None:
    if summary.alert_context.host_label is not None:
        return summary.alert_context.host_label
    if summary.alert_context.include_hostname_in_alerts:
        hostname = socket.gethostname().strip()
        return hostname or None
    return None
