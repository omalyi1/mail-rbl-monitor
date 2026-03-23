from enum import StrEnum


class AppEnvironment(StrEnum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class ListingStatus(StrEnum):
    CLEAN = "clean"
    LISTED = "listed"
    ERROR = "error"


class ProviderErrorKind(StrEnum):
    OPEN_RESOLVER = "open_resolver"
    TIMEOUT = "timeout"
    NO_ANSWER = "no_answer"
    NO_NAMESERVERS = "no_nameservers"
    DNS_EXCEPTION = "dns_exception"
    UNEXPECTED = "unexpected"


class NotificationChannel(StrEnum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
