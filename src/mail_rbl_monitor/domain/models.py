from __future__ import annotations

import re
from dataclasses import dataclass
from ipaddress import AddressValueError, IPv4Address
from typing import Self

from mail_rbl_monitor.domain.enums import AppEnvironment, ListingStatus, NotificationChannel
from mail_rbl_monitor.domain.exceptions import ConfigurationError

_PROVIDER_NAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


@dataclass(frozen=True, slots=True)
class TargetIP:
    value: IPv4Address

    @classmethod
    def from_raw(cls, value: IPv4Address | str) -> Self:
        if isinstance(value, IPv4Address):
            return cls(value=value)

        try:
            return cls(value=IPv4Address(value))
        except AddressValueError as exc:
            raise ConfigurationError(f"Invalid IPv4 address: {value}") from exc

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class DnsblProvider:
    name: str

    @classmethod
    def from_raw(cls, value: str) -> Self:
        normalized = value.strip().lower()
        if not normalized:
            raise ConfigurationError("DNSBL provider names must not be empty.")
        if not _PROVIDER_NAME_PATTERN.fullmatch(normalized):
            raise ConfigurationError(f"Invalid DNSBL provider name: {value}")
        return cls(name=normalized)

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    target_ip: TargetIP
    provider: DnsblProvider
    status: ListingStatus
    response_detail: str | None = None


@dataclass(frozen=True, slots=True)
class AppRuntimeConfigSummary:
    environment: AppEnvironment
    log_level: str
    timeout_seconds: int
    dry_run: bool
    target_ips: tuple[TargetIP, ...]
    providers: tuple[DnsblProvider, ...]
    telegram_enabled: bool
    discord_enabled: bool
    enabled_channels: tuple[NotificationChannel, ...]

    @property
    def target_count(self) -> int:
        return len(self.target_ips)

    @property
    def provider_count(self) -> int:
        return len(self.providers)
