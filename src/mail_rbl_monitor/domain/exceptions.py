from mail_rbl_monitor.domain.enums import NotificationChannel, ProviderErrorKind


class MailRblMonitorError(Exception):
    """Base exception for the service."""


class ConfigurationError(MailRblMonitorError):
    """Raised when environment-driven configuration is invalid."""


class ProviderResolutionError(MailRblMonitorError):
    """Raised when a DNSBL provider lookup cannot be completed."""

    def __init__(self, message: str, *, error_kind: ProviderErrorKind) -> None:
        super().__init__(message)
        self.error_kind = error_kind


class NotificationError(MailRblMonitorError):
    """Raised when a notification channel cannot deliver a message."""

    def __init__(
        self,
        message: str,
        *,
        stage: str = "notification",
        failed_channel: NotificationChannel | None = None,
        attempted_notification_channels: tuple[NotificationChannel, ...] = (),
        notifications_sent_before_failure: tuple[NotificationChannel, ...] = (),
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.failed_channel = failed_channel
        self.attempted_notification_channels = attempted_notification_channels
        self.notifications_sent_before_failure = notifications_sent_before_failure
