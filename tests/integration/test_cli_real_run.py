from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from mail_rbl_monitor.cli import main
from mail_rbl_monitor.constants import ExitCode
from mail_rbl_monitor.domain.enums import ListingStatus, NotificationChannel
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
    assert "zen.spamhaus.org" in fake_sender.sent_messages[0]
