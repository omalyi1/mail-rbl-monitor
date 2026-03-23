from ipaddress import IPv4Address

import pytest

from mail_rbl_monitor.config import Settings, _parse_target_hosts_mapping, load_settings
from mail_rbl_monitor.domain.exceptions import ConfigurationError

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
    monkeypatch.setenv("MAIL_RBL_MONITOR_TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TELEGRAM_CHAT_ID", "")
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_DISCORD", "false")
    monkeypatch.setenv("MAIL_RBL_MONITOR_DISCORD_WEBHOOK_URL", "")
    monkeypatch.setenv("MAIL_RBL_MONITOR_HOST_LABEL", "")
    monkeypatch.setenv("MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS", "true")
    monkeypatch.setenv("MAIL_RBL_MONITOR_ALERT_TIMEZONE", "Etc/UTC")
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
    assert settings.include_checked_at_in_alerts is True
    assert settings.alert_timezone == "Etc/UTC"


def test_settings_parse_target_hosts_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv(
        "MAIL_RBL_MONITOR_TARGET_HOSTS",
        " 136.243.71.222 = mail.gol.ua ",
    )

    settings = load_settings()

    assert settings.target_hosts == {IPv4Address("136.243.71.222"): "mail.gol.ua"}


def test_target_hosts_parses_first_middle_and_last_entries() -> None:
    parsed = _parse_target_hosts_mapping(
        "136.243.71.222=mail.gol.ua,136.243.71.219=mail.gol.lt,116.202.172.25=mail.goland.ua"
    )

    assert parsed[IPv4Address("136.243.71.222")] == "mail.gol.ua"
    assert parsed[IPv4Address("136.243.71.219")] == "mail.gol.lt"
    assert parsed[IPv4Address("116.202.172.25")] == "mail.goland.ua"


def test_target_hosts_parser_rejects_malformed_entry() -> None:
    with pytest.raises(ValueError, match="ip=hostname"):
        _parse_target_hosts_mapping("136.243.71.222")


def test_target_hosts_parser_rejects_invalid_ip_key() -> None:
    with pytest.raises(ValueError, match="Invalid IPv4 address in target host mapping"):
        _parse_target_hosts_mapping("999.243.71.222=mail.gol.ua")


def test_target_hosts_parser_rejects_empty_hostname() -> None:
    with pytest.raises(ValueError, match="hostname must not be empty"):
        _parse_target_hosts_mapping("136.243.71.222=")


def test_target_hosts_parser_rejects_duplicate_ips() -> None:
    with pytest.raises(ValueError, match="Duplicate target host mapping for IP"):
        _parse_target_hosts_mapping("136.243.71.222=mail.gol.ua,136.243.71.222=mail2.gol.ua")


def test_settings_accepts_valid_alert_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_ALERT_TIMEZONE", "Europe/Kyiv")

    settings = load_settings()

    assert settings.alert_timezone == "Europe/Kyiv"


def test_settings_accepts_new_canonical_checked_at_env_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS", "false")

    settings = load_settings()

    assert settings.include_checked_at_in_alerts is False


def test_settings_accepts_deprecated_checked_at_env_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings.model_validate(
        {
            "app_env": "dev",
            "app_log_level": "INFO",
            "target_ips": "136.243.71.222",
            "target_hosts": "",
            "dnsbl_providers": "zen.spamhaus.org,b.barracudacentral.org,bl.spamcop.net",
            "MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS": False,
            "alert_timezone": "Etc/UTC",
            "timeout_seconds": 5,
            "dry_run": True,
        }
    )

    assert settings.include_checked_at_in_alerts is False


def test_settings_prefers_canonical_checked_at_env_key_when_both_are_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS", "false")
    monkeypatch.setenv("MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS", "true")

    settings = load_settings()

    assert settings.include_checked_at_in_alerts is False


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


def test_settings_reject_invalid_alert_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_ALERT_TIMEZONE", "Not/ARealTimezone")

    with pytest.raises(ConfigurationError, match="alert_timezone"):
        load_settings()


def test_settings_rejects_malformed_target_host_mapping_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_HOSTS", "136.243.71.222")

    with pytest.raises(ConfigurationError, match="target_hosts"):
        load_settings()


def test_settings_rejects_invalid_target_host_mapping_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_HOSTS", "999.243.71.222=mail.gol.ua")

    with pytest.raises(ConfigurationError, match="target_hosts"):
        load_settings()


def test_settings_rejects_empty_target_host_mapping_hostname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_HOSTS", "136.243.71.222=")

    with pytest.raises(ConfigurationError, match="target_hosts"):
        load_settings()


def test_settings_rejects_target_host_mapping_ip_not_in_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_base_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_HOSTS", "136.243.71.219=mail.gol.lt")

    with pytest.raises(ConfigurationError, match="target_hosts"):
        load_settings()
