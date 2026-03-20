from __future__ import annotations

from collections.abc import Sequence
from ipaddress import IPv4Address
from typing import Protocol

from mail_rbl_monitor.domain.enums import NotificationChannel


class DnsResolverPort(Protocol):
    def resolve_a(self, query_name: str, timeout_seconds: int) -> Sequence[IPv4Address]:
        """Resolve A records for the supplied query name."""


class NotificationSenderPort(Protocol):
    @property
    def channel(self) -> NotificationChannel:
        """Return the notification channel handled by this adapter."""

    def send(self, message: str) -> None:
        """Send a notification message through the configured channel."""
