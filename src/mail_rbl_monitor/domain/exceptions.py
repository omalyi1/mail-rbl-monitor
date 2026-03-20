from mail_rbl_monitor.domain.enums import ProviderErrorKind


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
