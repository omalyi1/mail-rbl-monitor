from __future__ import annotations

from collections.abc import Sequence

_REDACTED_VALUE = "[REDACTED]"


def sanitize_operator_error_message(
    message: str,
    *,
    secret_values: Sequence[str],
    fallback: str,
) -> str:
    normalized = message.strip()
    if not normalized:
        return fallback
    return redact_secret_values(normalized, secret_values=secret_values)


def redact_secret_values(text: str, *, secret_values: Sequence[str]) -> str:
    redacted = text
    for secret_value in _normalized_secret_values(secret_values):
        redacted = redacted.replace(secret_value, _REDACTED_VALUE)
    return redacted


def _normalized_secret_values(secret_values: Sequence[str]) -> tuple[str, ...]:
    normalized = {value.strip() for value in secret_values if value.strip()}
    return tuple(sorted(normalized, key=len, reverse=True))
