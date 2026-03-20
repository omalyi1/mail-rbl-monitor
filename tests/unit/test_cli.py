import pytest

from mail_rbl_monitor.cli import main
from mail_rbl_monitor.constants import ExitCode

_ENV_KEYS = (
    "APP_ENV",
    "APP_LOG_LEVEL",
    "MAIL_RBL_MONITOR_TARGET_IPS",
    "MAIL_RBL_MONITOR_DNSBL_PROVIDERS",
    "MAIL_RBL_MONITOR_ENABLE_TELEGRAM",
    "MAIL_RBL_MONITOR_TELEGRAM_BOT_TOKEN",
    "MAIL_RBL_MONITOR_TELEGRAM_CHAT_ID",
    "MAIL_RBL_MONITOR_ENABLE_DISCORD",
    "MAIL_RBL_MONITOR_DISCORD_WEBHOOK_URL",
    "MAIL_RBL_MONITOR_TIMEOUT_SECONDS",
    "MAIL_RBL_MONITOR_DRY_RUN",
)


def _set_base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("APP_LOG_LEVEL", "INFO")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_IPS", "136.243.71.222")
    monkeypatch.setenv(
        "MAIL_RBL_MONITOR_DNSBL_PROVIDERS",
        "zen.spamhaus.org,b.barracudacentral.org,bl.spamcop.net",
    )
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_TELEGRAM", "false")
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_DISCORD", "false")
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
