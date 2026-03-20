from enum import StrEnum


class AppEnvironment(StrEnum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class ListingStatus(StrEnum):
    CLEAN = "clean"
    LISTED = "listed"
    ERROR = "error"


class NotificationChannel(StrEnum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
