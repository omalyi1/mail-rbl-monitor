from __future__ import annotations

from dataclasses import dataclass

import httpx

from mail_rbl_monitor.domain.enums import NotificationChannel
from mail_rbl_monitor.domain.exceptions import NotificationError
from mail_rbl_monitor.domain.ports import NotificationSenderPort


@dataclass(frozen=True, slots=True)
class TelegramNotificationSender(NotificationSenderPort):
    bot_token: str
    chat_id: str
    timeout_seconds: int

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.TELEGRAM

    def send(self, message: str) -> None:
        try:
            with httpx.Client(timeout=float(self.timeout_seconds)) as client:
                response = client.post(
                    self._url,
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                    },
                )
                response.raise_for_status()
                response_payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise NotificationError(
                (
                    "Telegram notification delivery failed with "
                    f"HTTP status {exc.response.status_code}."
                ),
                failed_channel=self.channel,
            ) from exc
        except httpx.HTTPError as exc:
            raise NotificationError(
                f"Telegram notification delivery failed with {exc.__class__.__name__}.",
                failed_channel=self.channel,
            ) from exc
        except ValueError as exc:
            raise NotificationError(
                "Telegram notification delivery returned an invalid response.",
                failed_channel=self.channel,
            ) from exc

        if not isinstance(response_payload, dict) or response_payload.get("ok") is False:
            raise NotificationError(
                "Telegram notification delivery was rejected by the Telegram API.",
                failed_channel=self.channel,
            )

    @property
    def _url(self) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
