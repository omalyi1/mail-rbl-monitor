from __future__ import annotations

from dataclasses import dataclass

import httpx

from mail_rbl_monitor.domain.enums import NotificationChannel
from mail_rbl_monitor.domain.exceptions import NotificationError
from mail_rbl_monitor.domain.ports import NotificationSenderPort


@dataclass(frozen=True, slots=True)
class DiscordNotificationSender(NotificationSenderPort):
    webhook_url: str
    timeout_seconds: int

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.DISCORD

    def send(self, message: str) -> None:
        try:
            with httpx.Client(timeout=float(self.timeout_seconds)) as client:
                response = client.post(
                    self.webhook_url,
                    json={"content": message},
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise NotificationError(
                (
                    "Discord notification delivery failed with "
                    f"HTTP status {exc.response.status_code}."
                ),
                failed_channel=self.channel,
            ) from exc
        except httpx.HTTPError as exc:
            raise NotificationError(
                f"Discord notification delivery failed with {exc.__class__.__name__}.",
                failed_channel=self.channel,
            ) from exc
