from __future__ import annotations

import json
import logging

import httpx
import pytest
import respx

from mail_rbl_monitor.domain.exceptions import NotificationError
from mail_rbl_monitor.infrastructure.notifications.discord import DiscordNotificationSender
from mail_rbl_monitor.infrastructure.notifications.telegram import TelegramNotificationSender
from mail_rbl_monitor.logging import configure_logging


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

    with pytest.raises(NotificationError, match="delivery failed with HTTP status 500") as exc_info:
        sender.send("listing detected")

    assert "secret-token" not in str(exc_info.value)


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

    with pytest.raises(NotificationError, match="delivery failed with HTTP status 500") as exc_info:
        sender.send("listing detected")

    assert "https://discord.example/webhook" not in str(exc_info.value)


@respx.mock
def test_discord_sender_raises_secret_safe_notification_error_on_transport_failure() -> None:
    respx.post("https://discord.example/secret-webhook").mock(
        side_effect=httpx.ConnectError(
            "boom https://discord.example/secret-webhook",
            request=httpx.Request("POST", "https://discord.example/secret-webhook"),
        )
    )
    sender = DiscordNotificationSender(
        webhook_url="https://discord.example/secret-webhook",
        timeout_seconds=5,
    )

    with pytest.raises(NotificationError) as exc_info:
        sender.send("listing detected")

    assert "https://discord.example/secret-webhook" not in str(exc_info.value)


@respx.mock
def test_telegram_sender_raises_secret_safe_notification_error_on_transport_failure() -> None:
    telegram_url = "https://api.telegram.org/botsecret-token/sendMessage"
    respx.post(telegram_url).mock(
        side_effect=httpx.ConnectError(
            f"boom {telegram_url}",
            request=httpx.Request("POST", telegram_url),
        )
    )
    sender = TelegramNotificationSender(
        bot_token="secret-token",
        chat_id="123456",
        timeout_seconds=5,
    )

    with pytest.raises(NotificationError) as exc_info:
        sender.send("listing detected")

    assert "secret-token" not in str(exc_info.value)
    assert telegram_url not in str(exc_info.value)


def test_configure_logging_suppresses_httpx_request_loggers(
    caplog: pytest.LogCaptureFixture,
) -> None:
    configure_logging("INFO")
    httpx_logger = logging.getLogger("httpx")
    httpcore_logger = logging.getLogger("httpcore")

    assert httpx_logger.level == logging.WARNING
    assert httpcore_logger.level == logging.WARNING

    caplog.set_level(logging.INFO)
    httpx_logger.info("HTTP Request: POST https://api.telegram.org/botsecret-token/sendMessage")
    httpcore_logger.info("HTTP Request: POST https://discord.com/api/webhooks/1/secret-token")

    assert "botsecret-token" not in caplog.text
    assert "secret-token" not in caplog.text
