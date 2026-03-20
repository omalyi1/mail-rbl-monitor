from ipaddress import IPv4Address

import pytest

from mail_rbl_monitor.config import load_settings
from mail_rbl_monitor.domain.exceptions import ConfigurationError

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
    "MAIL_RBL_MONITOR_HOST_LABEL",
    "MAIL_RBL_MONITOR_INCLUDE_HOSTNAME_IN_ALERTS",
    "MAIL_RBL_MONITOR_INCLUDE_ENVIRONMENT_IN_ALERTS",
    "MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS",
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


def test_settings_parses_single_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_base_env(monkeypatch)

    settings = load_settings()

    assert settings.target_ips == (IPv4Address("136.243.71.222"),)
    assert settings.dnsbl_providers == (
        "zen.spamhaus.org",
        "b.barracudacentral.org",
        "bl.spamcop.net",
    )
    assert settings.timeout_seconds == 5
    assert settings.dry_run is True
    assert settings.host_label is None
    assert settings.include_hostname_in_alerts is True
    assert settings.include_environment_in_alerts is True
    assert settings.include_utc_timestamp_in_alerts is True


def test_settings_rejects_invalid_ipv4(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_IPS", "999.243.71.222")

    with pytest.raises(ConfigurationError, match="target_ips"):
        load_settings()


def test_settings_require_telegram_credentials_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_TELEGRAM", "true")

    with pytest.raises(ConfigurationError, match="Telegram credentials are required"):
        load_settings()
