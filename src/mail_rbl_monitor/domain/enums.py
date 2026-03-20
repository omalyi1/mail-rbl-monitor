from enum import StrEnum


class AppEnvironment(StrEnum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class ListingStatus(StrEnum):
    LISTED = "listed"
    NOT_LISTED = "not_listed"
    UNKNOWN = "unknown"


class NotificationChannel(StrEnum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
