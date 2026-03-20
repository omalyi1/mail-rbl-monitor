from enum import IntEnum

APP_NAME = "mail-rbl-monitor"
APP_DESCRIPTION = "Deterministic DNSBL reputation monitor for mail servers."
LOGGER_NAME = "mail_rbl_monitor"
DEFAULT_ENV_FILE = ".env"
DEFAULT_TIMEOUT_SECONDS = 5
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 30


class ExitCode(IntEnum):
    SUCCESS = 0
    FAILURE = 1
    LISTING_FOUND = 20
    PROVIDER_ERRORS = 30
