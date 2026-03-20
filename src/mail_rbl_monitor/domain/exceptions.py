class MailRblMonitorError(Exception):
    """Base exception for the service."""


class ConfigurationError(MailRblMonitorError):
    """Raised when environment-driven configuration is invalid."""


class ProviderResolutionError(MailRblMonitorError):
    """Raised when a DNSBL provider lookup cannot be completed."""


class NotificationError(MailRblMonitorError):
    """Raised when a notification channel cannot deliver a message."""
