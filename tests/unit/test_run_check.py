from __future__ import annotations

from dataclasses import dataclass, field

from mail_rbl_monitor.application.run_check import run_check
from mail_rbl_monitor.cli import determine_exit_code
from mail_rbl_monitor.config import Settings
from mail_rbl_monitor.constants import ExitCode
from mail_rbl_monitor.domain.enums import (
    AppEnvironment,
    ListingStatus,
    NotificationChannel,
    ProviderErrorKind,
)
from mail_rbl_monitor.domain.models import DnsblProvider, ProviderCheckResult, TargetIP
from mail_rbl_monitor.infrastructure.dns.resolver import build_dnsbl_query_name


class FakeDnsResolver:
    def __init__(self, results: dict[tuple[str, str], ProviderCheckResult]) -> None:
        self._results = results
        self.calls: list[tuple[str, str, int]] = []

    def check_provider(
        self, target_ip: TargetIP, provider: DnsblProvider, timeout_seconds: int
    ) -> ProviderCheckResult:
        self.calls.append((str(target_ip), provider.name, timeout_seconds))
        return self._results[(str(target_ip), provider.name)]


@dataclass(slots=True)
class FakeNotificationSender:
    _channel: NotificationChannel
    sent_messages: list[str] = field(default_factory=list)

    @property
    def channel(self) -> NotificationChannel:
        return self._channel

    def send(self, message: str) -> None:
        self.sent_messages.append(message)


def _build_settings(
    *,
    dry_run: bool = False,
    enable_telegram: bool = False,
    enable_discord: bool = False,
) -> Settings:
    return Settings.model_validate(
        {
            "app_env": AppEnvironment.TEST,
            "app_log_level": "INFO",
            "target_ips": ["136.243.71.222"],
            "dnsbl_providers": ["zen.spamhaus.org"],
            "enable_telegram": enable_telegram,
            "telegram_bot_token": "telegram-token" if enable_telegram else None,
            "telegram_chat_id": "123456" if enable_telegram else None,
            "enable_discord": enable_discord,
            "discord_webhook_url": "https://discord.example/webhook" if enable_discord else None,
            "timeout_seconds": 5,
            "dry_run": dry_run,
        }
    )


def _build_provider_result(
    *,
    status: ListingStatus,
    listed_addresses: tuple[str, ...] = (),
    txt_reasons: tuple[str, ...] = (),
    error_message: str | None = None,
    error_kind: ProviderErrorKind | None = None,
) -> ProviderCheckResult:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    return ProviderCheckResult(
        target_ip=target_ip,
        provider=provider,
        query_name=build_dnsbl_query_name(target_ip.value, provider.name),
        status=status,
        listed_addresses=listed_addresses,
        txt_reasons=txt_reasons,
        error_message=error_message,
        error_kind=error_kind,
        latency_ms=12,
    )


def test_application_clean_run_returns_success_without_notifications() -> None:
    settings = _build_settings(dry_run=False)
    resolver = FakeDnsResolver(
        {("136.243.71.222", "zen.spamhaus.org"): _build_provider_result(status=ListingStatus.CLEAN)}
    )
    sender = FakeNotificationSender(NotificationChannel.TELEGRAM)

    summary = run_check(settings, dns_resolver=resolver, notification_senders=(sender,))

    assert summary.has_listings is False
    assert summary.has_errors is False
    assert summary.notifications_sent == ()
    assert sender.sent_messages == []
    assert summary.checked_at_utc.endswith("Z")
    assert determine_exit_code(summary) == ExitCode.SUCCESS


def test_application_listed_run_sends_notifications_and_returns_listing_exit_code() -> None:
    settings = _build_settings(dry_run=False, enable_telegram=True, enable_discord=True)
    resolver = FakeDnsResolver(
        {
            ("136.243.71.222", "zen.spamhaus.org"): _build_provider_result(
                status=ListingStatus.LISTED,
                listed_addresses=("127.0.0.2",),
                txt_reasons=("Spamhaus listed",),
            )
        }
    )
    telegram_sender = FakeNotificationSender(NotificationChannel.TELEGRAM)
    discord_sender = FakeNotificationSender(NotificationChannel.DISCORD)

    summary = run_check(
        settings,
        dns_resolver=resolver,
        notification_senders=(telegram_sender, discord_sender),
    )

    assert summary.has_listings is True
    assert summary.notifications_sent == (
        NotificationChannel.TELEGRAM,
        NotificationChannel.DISCORD,
    )
    assert summary.alert_message is not None
    assert "Environment: test" in summary.alert_message
    assert "Checked at (UTC): " in summary.alert_message
    assert "Target IP: 136.243.71.222" in summary.alert_message
    assert "Spamhaus ZEN (zen.spamhaus.org)" in summary.alert_message
    assert telegram_sender.sent_messages == [summary.alert_message]
    assert discord_sender.sent_messages == [summary.alert_message]
    assert determine_exit_code(summary) == ExitCode.LISTING_FOUND


def test_application_provider_error_only_run_returns_degraded_exit_code() -> None:
    settings = _build_settings(dry_run=False)
    resolver = FakeDnsResolver(
        {
            ("136.243.71.222", "zen.spamhaus.org"): _build_provider_result(
                status=ListingStatus.ERROR,
                error_message="DNS query timed out.",
                error_kind=ProviderErrorKind.TIMEOUT,
            )
        }
    )
    sender = FakeNotificationSender(NotificationChannel.TELEGRAM)

    summary = run_check(settings, dns_resolver=resolver, notification_senders=(sender,))

    assert summary.has_listings is False
    assert summary.has_errors is True
    assert summary.error_count == 1
    assert summary.error_results[0].error_kind == ProviderErrorKind.TIMEOUT
    assert sender.sent_messages == []
    assert determine_exit_code(summary) == ExitCode.PROVIDER_ERRORS
