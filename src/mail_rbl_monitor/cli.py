from __future__ import annotations

import argparse
import logging
import socket
import sys
from collections.abc import Sequence

from mail_rbl_monitor import __version__
from mail_rbl_monitor.application.run_check import run_check
from mail_rbl_monitor.config import Settings, load_settings
from mail_rbl_monitor.constants import APP_DESCRIPTION, APP_NAME, LOGGER_NAME, ExitCode
from mail_rbl_monitor.domain.exceptions import (
    ConfigurationError,
    MailRblMonitorError,
    NotificationError,
)
from mail_rbl_monitor.domain.models import RunSummary
from mail_rbl_monitor.domain.services import current_utc_timestamp
from mail_rbl_monitor.logging import configure_logging
from mail_rbl_monitor.presentation.redaction import sanitize_operator_error_message
from mail_rbl_monitor.presentation.serializers import (
    RunPayload,
    dump_json_payload,
    serialize_failure,
    serialize_run_summary,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=APP_NAME, description=APP_DESCRIPTION)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run mode for this invocation regardless of environment configuration.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a stable machine-readable JSON summary to stdout.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings: Settings | None = None
    effective_settings: Settings | None = None

    try:
        settings = load_settings()
        configure_logging(settings.app_log_level)

        effective_settings = (
            settings.apply_cli_overrides(dry_run=True) if args.dry_run else settings
        )
        run_summary = run_check(effective_settings)
        exit_code = determine_exit_code(run_summary)

        if args.json:
            _write_json_payload(serialize_run_summary(run_summary, exit_code=int(exit_code)))

        return exit_code
    except ConfigurationError as exc:
        configure_logging("ERROR")
        safe_error_message = _safe_error_message(
            exc,
            settings=effective_settings or settings,
            fallback="Configuration validation failed.",
        )
        logging.getLogger(LOGGER_NAME).error(
            "Configuration validation failed",
            extra={"event": "config.error", "error": safe_error_message},
        )
        if args.json:
            _write_json_payload(
                serialize_failure(
                    exit_code=int(ExitCode.FAILURE),
                    error_type="configuration_error",
                    error_message=safe_error_message,
                    checked_at_utc=current_utc_timestamp(),
                    environment=_resolve_environment(settings=effective_settings or settings),
                    dry_run=_resolve_dry_run(
                        settings=effective_settings or settings,
                        cli_dry_run_override=args.dry_run,
                    ),
                    host_label=_resolve_host_label(settings=effective_settings or settings),
                    targets=_resolve_targets(settings=effective_settings or settings),
                    providers=_resolve_providers(settings=effective_settings or settings),
                )
            )
        return ExitCode.FAILURE
    except NotificationError as exc:
        configure_logging("ERROR")
        safe_error_message = _safe_error_message(
            exc,
            settings=effective_settings or settings,
            fallback="Notification delivery failed.",
        )
        logging.getLogger(LOGGER_NAME).error(
            "Notification delivery failed",
            extra={
                "event": "notification.error",
                "error": safe_error_message,
                "stage": exc.stage,
                "failed_channel": exc.failed_channel.value if exc.failed_channel else None,
                "attempted_notification_channels": [
                    channel.value for channel in exc.attempted_notification_channels
                ],
                "notifications_sent_before_failure": [
                    channel.value for channel in exc.notifications_sent_before_failure
                ],
            },
        )
        if args.json:
            _write_json_payload(
                serialize_failure(
                    exit_code=int(ExitCode.FAILURE),
                    error_type="notification_error",
                    error_message=safe_error_message,
                    checked_at_utc=current_utc_timestamp(),
                    environment=_resolve_environment(settings=effective_settings or settings),
                    dry_run=_resolve_dry_run(
                        settings=effective_settings or settings,
                        cli_dry_run_override=args.dry_run,
                    ),
                    host_label=_resolve_host_label(settings=effective_settings or settings),
                    targets=_resolve_targets(settings=effective_settings or settings),
                    providers=_resolve_providers(settings=effective_settings or settings),
                    stage=exc.stage,
                    failed_channel=exc.failed_channel,
                    attempted_notification_channels=exc.attempted_notification_channels,
                    notifications_sent_before_failure=exc.notifications_sent_before_failure,
                )
            )
        return ExitCode.FAILURE
    except MailRblMonitorError as exc:
        configure_logging("ERROR")
        safe_error_message = _safe_error_message(
            exc,
            settings=effective_settings or settings,
            fallback="Application failure.",
        )
        logging.getLogger(LOGGER_NAME).error(
            "Application error",
            extra={
                "event": "app.error",
                "error": safe_error_message,
                "error_type": exc.__class__.__name__,
            },
        )
        if args.json:
            _write_json_payload(
                serialize_failure(
                    exit_code=int(ExitCode.FAILURE),
                    error_type="application_error",
                    error_message=safe_error_message,
                    checked_at_utc=current_utc_timestamp(),
                    environment=_resolve_environment(settings=effective_settings or settings),
                    dry_run=_resolve_dry_run(
                        settings=effective_settings or settings,
                        cli_dry_run_override=args.dry_run,
                    ),
                    host_label=_resolve_host_label(settings=effective_settings or settings),
                    targets=_resolve_targets(settings=effective_settings or settings),
                    providers=_resolve_providers(settings=effective_settings or settings),
                )
            )
        return ExitCode.FAILURE
    except Exception:
        configure_logging("ERROR")
        logging.getLogger(LOGGER_NAME).exception(
            "Unexpected application failure",
            extra={"event": "app.error"},
        )
        if args.json:
            _write_json_payload(
                serialize_failure(
                    exit_code=int(ExitCode.FAILURE),
                    error_type="unexpected_error",
                    error_message="Unexpected application failure.",
                    checked_at_utc=current_utc_timestamp(),
                    environment=_resolve_environment(settings=effective_settings or settings),
                    dry_run=_resolve_dry_run(
                        settings=effective_settings or settings,
                        cli_dry_run_override=args.dry_run,
                    ),
                    host_label=_resolve_host_label(settings=effective_settings or settings),
                    targets=_resolve_targets(settings=effective_settings or settings),
                    providers=_resolve_providers(settings=effective_settings or settings),
                )
            )
        return ExitCode.FAILURE


def determine_exit_code(run_summary: RunSummary) -> ExitCode:
    if run_summary.has_listings:
        return ExitCode.LISTING_FOUND
    if run_summary.has_errors:
        return ExitCode.PROVIDER_ERRORS
    return ExitCode.SUCCESS


def _write_json_payload(payload: RunPayload) -> None:
    sys.stdout.write(f"{dump_json_payload(payload)}\n")


def _resolve_environment(*, settings: Settings | None) -> str | None:
    if settings is None:
        return None
    return settings.app_env.value


def _resolve_dry_run(*, settings: Settings | None, cli_dry_run_override: bool) -> bool | None:
    if settings is not None:
        return settings.dry_run
    if cli_dry_run_override:
        return True
    return None


def _resolve_host_label(*, settings: Settings | None) -> str | None:
    if settings is None:
        return None
    if settings.host_label is not None:
        return settings.host_label
    if settings.include_hostname_in_alerts:
        hostname = socket.gethostname().strip()
        return hostname or None
    return None


def _resolve_targets(*, settings: Settings | None) -> list[str]:
    if settings is None:
        return []
    return [str(target_ip) for target_ip in settings.target_ips]


def _resolve_providers(*, settings: Settings | None) -> list[str]:
    if settings is None:
        return []
    return list(settings.dnsbl_providers)


def _safe_error_message(
    error: BaseException,
    *,
    settings: Settings | None,
    fallback: str,
) -> str:
    return sanitize_operator_error_message(
        str(error),
        secret_values=settings.operator_secret_values() if settings is not None else (),
        fallback=fallback,
    )
