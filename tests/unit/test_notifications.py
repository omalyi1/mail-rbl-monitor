from __future__ import annotations

import json

import httpx
import pytest
import respx

from mail_rbl_monitor.domain.exceptions import NotificationError
from mail_rbl_monitor.infrastructure.notifications.discord import DiscordNotificationSender
from mail_rbl_monitor.infrastructure.notifications.telegram import TelegramNotificationSender


@respx.mock
def test_telegram_sender_posts_expected_payload() -> None:
    route = respx.post("https://api.telegram.org/botsecret-token/sendMessage").mock(
        return_value=httpx.Response(200, json={"ok": True, "result": {}})
    )
    sender = TelegramNotificationSender(
        bot_token="secret-token",
        chat_id="123456",
        timeout_seconds=5,
    )

    sender.send("listing detected")

    assert route.called
    request = route.calls.last.request
    assert json.loads(request.content) == {
        "chat_id": "123456",
        "text": "listing detected",
    }


@respx.mock
def test_telegram_sender_raises_notification_error_on_non_2xx() -> None:
    respx.post("https://api.telegram.org/botsecret-token/sendMessage").mock(
        return_value=httpx.Response(500, json={"ok": False})
    )
    sender = TelegramNotificationSender(
        bot_token="secret-token",
        chat_id="123456",
        timeout_seconds=5,
    )

    with pytest.raises(NotificationError, match="HTTP status 500"):
        sender.send("listing detected")


@respx.mock
def test_discord_sender_posts_expected_payload() -> None:
    route = respx.post("https://discord.example/webhook").mock(return_value=httpx.Response(204))
    sender = DiscordNotificationSender(
        webhook_url="https://discord.example/webhook",
        timeout_seconds=5,
    )

    sender.send("listing detected")

    assert route.called
    request = route.calls.last.request
    assert json.loads(request.content) == {"content": "listing detected"}


@respx.mock
def test_discord_sender_raises_notification_error_on_non_2xx() -> None:
    respx.post("https://discord.example/webhook").mock(
        return_value=httpx.Response(500, text="boom")
    )
    sender = DiscordNotificationSender(
        webhook_url="https://discord.example/webhook",
        timeout_seconds=5,
    )

    with pytest.raises(NotificationError, match="HTTP status 500"):
        sender.send("listing detected")
