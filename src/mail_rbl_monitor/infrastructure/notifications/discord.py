from __future__ import annotations

from dataclasses import dataclass

from mail_rbl_monitor.domain.enums import NotificationChannel
from mail_rbl_monitor.domain.exceptions import NotificationError
from mail_rbl_monitor.domain.ports import NotificationSenderPort


@dataclass(frozen=True, slots=True)
class DiscordNotificationSender(NotificationSenderPort):
    webhook_url: str

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.DISCORD

    def send(self, message: str) -> None:
        raise NotificationError(
            "Discord delivery is not implemented in Phase 1. "
            f"Refused to send message of length {len(message)}."
        )
