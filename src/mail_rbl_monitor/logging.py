from __future__ import annotations

import json
import logging
import time
from typing import Final, override

_RESERVED_LOG_RECORD_ATTRS: Final[frozenset[str]] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "event",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


def _serialize_log_value(value: object) -> str:
    return json.dumps(value, default=str, separators=(",", ":"))


class KeyValueFormatter(logging.Formatter):
    default_time_format = "%Y-%m-%dT%H:%M:%S"
    default_msec_format = "%s.%03dZ"

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        fields: list[str] = [
            f"ts={self.formatTime(record, self.datefmt)}",
            f"level={record.levelname}",
            f"logger={record.name}",
        ]

        event_name = getattr(record, "event", None)
        if isinstance(event_name, str) and event_name:
            fields.append(f"event={event_name}")

        fields.append(f"message={_serialize_log_value(message)}")

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED_LOG_RECORD_ATTRS and not key.startswith("_")
        }

        for key in sorted(extras):
            fields.append(f"{key}={_serialize_log_value(extras[key])}")

        if record.exc_info is not None and record.exc_info[0] is not None:
            fields.append(f"exc_type={record.exc_info[0].__name__}")

        return " ".join(fields)

    @override
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        timestamp = time.gmtime(record.created)
        if datefmt is not None:
            return time.strftime(datefmt, timestamp)

        formatted_time = time.strftime(self.default_time_format, timestamp)
        return self.default_msec_format % (formatted_time, record.msecs)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(KeyValueFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level.upper())
    root_logger.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.captureWarnings(True)
