from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest

from mail_rbl_monitor.cli import main
from mail_rbl_monitor.constants import ExitCode
from mail_rbl_monitor.domain.enums import ListingStatus, NotificationChannel
from mail_rbl_monitor.domain.exceptions import NotificationError
from mail_rbl_monitor.domain.models import DnsblProvider, ProviderCheckResult, TargetIP
from mail_rbl_monitor.infrastructure.dns.resolver import build_dnsbl_query_name

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


class FakeDnsResolver:
    def __init__(self, result: ProviderCheckResult) -> None:
        self._result = result

    def check_provider(
        self, target_ip: TargetIP, provider: DnsblProvider, timeout_seconds: int
    ) -> ProviderCheckResult:
        assert str(target_ip) == "136.243.71.222"
        assert provider.name == "zen.spamhaus.org"
        assert timeout_seconds == 5
        return self._result


@dataclass(slots=True)
class FakeNotificationSender:
    _channel: NotificationChannel
    sent_messages: list[str] = field(default_factory=list)

    @property
    def channel(self) -> NotificationChannel:
        return self._channel

    def send(self, message: str) -> None:
        self.sent_messages.append(message)


@dataclass(slots=True)
class FailingNotificationSender:
    _channel: NotificationChannel
    error_message: str

    @property
    def channel(self) -> NotificationChannel:
        return self._channel

    def send(self, message: str) -> None:
        raise NotificationError(self.error_message, failed_channel=self.channel)


def _set_real_run_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_LOG_LEVEL", "INFO")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TARGET_IPS", "136.243.71.222")
    monkeypatch.setenv("MAIL_RBL_MONITOR_DNSBL_PROVIDERS", "zen.spamhaus.org")
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_TELEGRAM", "true")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TELEGRAM_CHAT_ID", "123456")
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_DISCORD", "false")
    monkeypatch.setenv("MAIL_RBL_MONITOR_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("MAIL_RBL_MONITOR_DRY_RUN", "false")


def test_cli_real_run_returns_listing_exit_code_with_mocked_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_real_run_env(monkeypatch)
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    result = ProviderCheckResult(
        target_ip=target_ip,
        provider=provider,
        query_name=build_dnsbl_query_name(target_ip.value, provider.name),
        status=ListingStatus.LISTED,
        listed_addresses=("127.0.0.2",),
        txt_reasons=("Spamhaus listed",),
        latency_ms=10,
    )
    fake_resolver = FakeDnsResolver(result)
    fake_sender = FakeNotificationSender(NotificationChannel.TELEGRAM)

    monkeypatch.setattr(
        "mail_rbl_monitor.application.run_check.DnsblResolver", lambda: fake_resolver
    )
    monkeypatch.setattr(
        "mail_rbl_monitor.application.run_check._build_notification_senders",
        lambda settings: (fake_sender,),
    )

    exit_code = main([])

    assert exit_code == ExitCode.LISTING_FOUND
    assert len(fake_sender.sent_messages) == 1
    assert "Spamhaus ZEN (zen.spamhaus.org)" in fake_sender.sent_messages[0]


def test_cli_json_real_run_returns_valid_json_and_hides_secrets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_real_run_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_HOST_LABEL", "mail-01")
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    result = ProviderCheckResult(
        target_ip=target_ip,
        provider=provider,
        query_name=build_dnsbl_query_name(target_ip.value, provider.name),
        status=ListingStatus.LISTED,
        listed_addresses=("127.0.0.2",),
        txt_reasons=("Spamhaus listed",),
        latency_ms=10,
    )
    fake_resolver = FakeDnsResolver(result)
    fake_sender = FakeNotificationSender(NotificationChannel.TELEGRAM)

    monkeypatch.setattr(
        "mail_rbl_monitor.application.run_check.DnsblResolver", lambda: fake_resolver
    )
    monkeypatch.setattr(
        "mail_rbl_monitor.application.run_check._build_notification_senders",
        lambda settings: (fake_sender,),
    )

    exit_code = main(["--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == ExitCode.LISTING_FOUND
    assert payload["exit_code"] == 20
    assert payload["host_label"] == "mail-01"
    assert payload["summary"]["listed_count"] == 1
    assert payload["summary"]["notifications_sent"] == ["telegram"]
    assert payload["results"][0]["provider_results"][0]["provider_display_name"] == "Spamhaus ZEN"
    assert "telegram-token" not in captured.out


def test_cli_json_notification_failure_returns_failure_payload_without_secrets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    discord_webhook_url = "https://discord.example/webhook/super-secret"
    _set_real_run_env(monkeypatch)
    monkeypatch.setenv("MAIL_RBL_MONITOR_ENABLE_DISCORD", "true")
    monkeypatch.setenv("MAIL_RBL_MONITOR_DISCORD_WEBHOOK_URL", discord_webhook_url)

    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    result = ProviderCheckResult(
        target_ip=target_ip,
        provider=provider,
        query_name=build_dnsbl_query_name(target_ip.value, provider.name),
        status=ListingStatus.LISTED,
        listed_addresses=("127.0.0.2",),
        latency_ms=10,
    )
    fake_resolver = FakeDnsResolver(result)
    telegram_sender = FakeNotificationSender(NotificationChannel.TELEGRAM)
    discord_sender = FailingNotificationSender(
        NotificationChannel.DISCORD,
        f"Discord notification delivery failed for webhook {discord_webhook_url}.",
    )

    monkeypatch.setattr(
        "mail_rbl_monitor.application.run_check.DnsblResolver", lambda: fake_resolver
    )
    monkeypatch.setattr(
        "mail_rbl_monitor.application.run_check._build_notification_senders",
        lambda settings: (telegram_sender, discord_sender),
    )

    exit_code = main(["--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    error = payload["error"]

    assert exit_code == ExitCode.FAILURE
    assert payload["exit_code"] == 1
    assert error["type"] == "notification_error"
    assert error["stage"] == "notification"
    assert error["failed_channel"] == "discord"
    assert error["attempted_notification_channels"] == ["telegram", "discord"]
    assert error["notifications_sent_before_failure"] == ["telegram"]
    assert "telegram-token" not in captured.out
    assert discord_webhook_url not in captured.out
    assert "telegram-token" not in captured.err
    assert discord_webhook_url not in captured.err
