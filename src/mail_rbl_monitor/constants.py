from enum import IntEnum

APP_NAME = "mail-rbl-monitor"
APP_DESCRIPTION = "Deterministic DNSBL reputation monitor bootstrap for mail servers."
LOGGER_NAME = "mail_rbl_monitor"
DEFAULT_ENV_FILE = ".env"
DEFAULT_TIMEOUT_SECONDS = 5
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 30


class ExitCode(IntEnum):
    SUCCESS = 0
    UNEXPECTED_ERROR = 1
    CONFIGURATION_ERROR = 2
