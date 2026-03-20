from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from mail_rbl_monitor import __version__
from mail_rbl_monitor.application.run_check import run_check
from mail_rbl_monitor.config import load_settings
from mail_rbl_monitor.constants import APP_DESCRIPTION, APP_NAME, LOGGER_NAME, ExitCode
from mail_rbl_monitor.domain.exceptions import ConfigurationError
from mail_rbl_monitor.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=APP_NAME, description=APP_DESCRIPTION)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run mode for this invocation regardless of environment configuration.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        settings = load_settings()
        configure_logging(settings.app_log_level)

        effective_settings = (
            settings.apply_cli_overrides(dry_run=True) if args.dry_run else settings
        )
        run_check(effective_settings)
        return ExitCode.SUCCESS
    except ConfigurationError as exc:
        configure_logging("ERROR")
        logging.getLogger(LOGGER_NAME).error(
            "Configuration validation failed",
            extra={"event": "config.error", "error": str(exc)},
        )
        return ExitCode.CONFIGURATION_ERROR
    except Exception:
        configure_logging("ERROR")
        logging.getLogger(LOGGER_NAME).exception(
            "Unexpected application failure",
            extra={"event": "app.error"},
        )
        return ExitCode.UNEXPECTED_ERROR
