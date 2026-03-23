from __future__ import annotations

import re
from dataclasses import dataclass
from ipaddress import AddressValueError, IPv4Address
from typing import Self

from mail_rbl_monitor.domain.enums import (
    AppEnvironment,
    ListingStatus,
    NotificationChannel,
    ProviderErrorKind,
)
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
class ProviderCheckResult:
    target_ip: TargetIP
    provider: DnsblProvider
    query_name: str
    status: ListingStatus
    listed_addresses: tuple[str, ...] = ()
    txt_reasons: tuple[str, ...] = ()
    error_message: str | None = None
    error_kind: ProviderErrorKind | None = None
    latency_ms: int | None = None

    @property
    def is_clean(self) -> bool:
        return self.status == ListingStatus.CLEAN

    @property
    def is_listed(self) -> bool:
        return self.status == ListingStatus.LISTED

    @property
    def is_error(self) -> bool:
        return self.status == ListingStatus.ERROR


@dataclass(frozen=True, slots=True)
class TargetCheckResult:
    target_ip: TargetIP
    provider_results: tuple[ProviderCheckResult, ...]

    @property
    def listed_results(self) -> tuple[ProviderCheckResult, ...]:
        return tuple(result for result in self.provider_results if result.is_listed)

    @property
    def error_results(self) -> tuple[ProviderCheckResult, ...]:
        return tuple(result for result in self.provider_results if result.is_error)

    @property
    def has_listings(self) -> bool:
        return bool(self.listed_results)

    @property
    def has_errors(self) -> bool:
        return bool(self.error_results)


@dataclass(frozen=True, slots=True)
class OperatorAlertContext:
    host_label: str | None
    include_hostname_in_alerts: bool
    include_utc_timestamp_in_alerts: bool
    alert_timezone: str


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
    alert_context: OperatorAlertContext

    @property
    def target_count(self) -> int:
        return len(self.target_ips)

    @property
    def provider_count(self) -> int:
        return len(self.providers)


@dataclass(frozen=True, slots=True)
class RunSummary:
    runtime_config: AppRuntimeConfigSummary
    checked_at_utc: str
    target_results: tuple[TargetCheckResult, ...] = ()
    host_label: str | None = None
    notifications_sent: tuple[NotificationChannel, ...] = ()
    alert_message: str | None = None

    @property
    def total_targets(self) -> int:
        return self.runtime_config.target_count

    @property
    def total_provider_checks(self) -> int:
        return sum(len(result.provider_results) for result in self.target_results)

    @property
    def listed_results(self) -> tuple[ProviderCheckResult, ...]:
        return tuple(
            provider_result
            for target_result in self.target_results
            for provider_result in target_result.provider_results
            if provider_result.is_listed
        )

    @property
    def error_results(self) -> tuple[ProviderCheckResult, ...]:
        return tuple(
            provider_result
            for target_result in self.target_results
            for provider_result in target_result.provider_results
            if provider_result.is_error
        )

    @property
    def listed_count(self) -> int:
        return len(self.listed_results)

    @property
    def error_count(self) -> int:
        return len(self.error_results)

    @property
    def has_listings(self) -> bool:
        return bool(self.listed_results)

    @property
    def has_errors(self) -> bool:
        return bool(self.error_results)
