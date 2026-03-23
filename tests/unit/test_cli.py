import json

import pytest

from mail_rbl_monitor.cli import determine_exit_code, main
from mail_rbl_monitor.constants import ExitCode
from mail_rbl_monitor.domain.enums import AppEnvironment
from mail_rbl_monitor.domain.models import AppRuntimeConfigSummary, OperatorAlertContext, RunSummary

_ENV_KEYS = (
    "APP_ENV",
    "APP_LOG_LEVEL",
    "MAIL_RBL_MONITOR_TARGET_IPS",
    "MAIL_RBL_MONITOR_TARGET_HOSTS",
    "MAIL_RBL_MONITOR_DNSBL_PROVIDERS",
    "MAIL_RBL_MONITOR_ENABLE_TELEGRAM",
    "MAIL_RBL_MONITOR_TELEGRAM_BOT_TOKEN",
    "MAIL_RBL_MONITOR_TELEGRAM_CHAT_ID",
    "MAIL_RBL_MONITOR_ENABLE_DISCORD",
    "MAIL_RBL_MONITOR_DISCORD_WEBHOOK_URL",
    "MAIL_RBL_MONITOR_HOST_LABEL",
    "MAIL_RBL_MONITOR_INCLUDE_HOSTNAME_IN_ALERTS",
    "MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS",
    "MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS",
    "MAIL_RBL_MONITOR_ALERT_TIMEZONE",
    "MAIL_RBL_MONITOR_TIMEOUT_SECONDS",
    "MAIL_RBL_MONITOR_DRY_RUN",
)


def _set_base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("APP_LOG_LEVEL", "INFO")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_IPS", "136.243.71.222")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_HOSTS", "")
    monkeypatch.setenv(
        "MAIL_RBL_MONITOR_DNSBL_PROVIDERS",
        "zen.spamhaus.org,b.barracudacentral.org,bl.spamcop.net",
    )
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_TELEGRAM", "false")
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_DISCORD", "false")
    monkeypatch.setenv("MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS", "true")
    monkeypatch.setenv("MAIL_RBL_MONITOR_ALERT_TIMEZONE", "Etc/UTC")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("MAIL_RBL_MONITOR_DRY_RUN", "true")


def test_cli_dry_run_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _set_base_env(monkeypatch)

    exit_code = main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == ExitCode.SUCCESS
    assert "Loaded configuration successfully" in captured.err
    assert "Targets configured" in captured.err
    assert "Dry run complete" in captured.err


def test_cli_dry_run_json_emits_valid_payload(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_HOST_LABEL", "mail-01")

    exit_code = main(["--dry-run", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == ExitCode.SUCCESS
    assert payload["app"] == "mail-rbl-monitor"
    assert payload["dry_run"] is True
    assert payload["environment"] == "dev"
    assert payload["host_label"] == "mail-01"
    assert payload["summary"]["total_provider_checks"] == 0
    assert payload["results"] == []
    assert payload["exit_code"] == 0
    assert payload["error"] is None


def test_determine_exit_code_returns_success_for_clean_summary() -> None:
    run_summary = RunSummary(
        runtime_config=AppRuntimeConfigSummary(
            environment=AppEnvironment.TEST,
            log_level="INFO",
            timeout_seconds=5,
            dry_run=False,
            target_ips=(),
            providers=(),
            telegram_enabled=False,
            discord_enabled=False,
            enabled_channels=(),
            alert_context=OperatorAlertContext(
                host_label=None,
                include_hostname_in_alerts=True,
                include_checked_at_in_alerts=True,
                alert_timezone="Etc/UTC",
            ),
        ),
        checked_at_utc="2026-03-20T09:00:00Z",
    )

    assert determine_exit_code(run_summary) == ExitCode.SUCCESS
