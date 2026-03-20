from __future__ import annotations

from typing import Protocol

from mail_rbl_monitor.domain.enums import NotificationChannel
from mail_rbl_monitor.domain.models import DnsblProvider, ProviderCheckResult, TargetIP


class DnsResolverPort(Protocol):
    def check_provider(
        self, target_ip: TargetIP, provider: DnsblProvider, timeout_seconds: int
    ) -> ProviderCheckResult:
        """Run a single DNSBL provider check for a target IP."""


class NotificationSenderPort(Protocol):
    @property
    def channel(self) -> NotificationChannel:
        """Return the notification channel handled by this adapter."""

    def send(self, message: str) -> None:
        """Send a notification message through the configured channel."""
