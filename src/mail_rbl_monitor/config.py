from __future__ import annotations

from collections.abc import Iterable
from ipaddress import IPv4Address
from typing import TYPE_CHECKING, Annotated, Self

from pydantic import (
    AliasChoices,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict, SettingsError

from mail_rbl_monitor.constants import (
    DEFAULT_ENV_FILE,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,
    MIN_TIMEOUT_SECONDS,
)
from mail_rbl_monitor.domain.enums import AppEnvironment
from mail_rbl_monitor.domain.exceptions import ConfigurationError
from mail_rbl_monitor.domain.models import DnsblProvider, OperatorAlertContext, TargetIP
from mail_rbl_monitor.domain.services import build_runtime_summary

_ALLOWED_LOG_LEVELS = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"})


def _split_csv(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        items = [str(item).strip() for item in value]
        return [item for item in items if item]
    raise TypeError("Expected a comma-separated string or sequence.")


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_prefix="MAIL_RBL_MONITOR_",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
        validate_default=True,
    )

    app_env: AppEnvironment = Field(
        default=AppEnvironment.DEV,
        validation_alias=AliasChoices("APP_ENV"),
    )
    app_log_level: str = Field(default="INFO", validation_alias=AliasChoices("APP_LOG_LEVEL"))
    target_ips: Annotated[tuple[IPv4Address, ...], NoDecode] = Field(default_factory=tuple)
    dnsbl_providers: Annotated[tuple[str, ...], NoDecode] = Field(default_factory=tuple)
    enable_telegram: bool = False
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: str | None = None
    enable_discord: bool = False
    discord_webhook_url: SecretStr | None = None
    host_label: str | None = None
    include_hostname_in_alerts: bool = True
    include_environment_in_alerts: bool = True
    include_utc_timestamp_in_alerts: bool = True
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    dry_run: bool = True

    @field_validator("app_env", mode="before")
    @classmethod
    def normalize_app_env(cls, value: object) -> object:
        return value.lower() if isinstance(value, str) else value

    @field_validator("app_log_level")
    @classmethod
    def validate_app_log_level(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in _ALLOWED_LOG_LEVELS:
            raise ValueError(
                "APP_LOG_LEVEL must be one of CRITICAL, ERROR, WARNING, INFO, or DEBUG."
            )
        return normalized

    @field_validator("target_ips", mode="before")
    @classmethod
    def parse_target_ips(cls, value: object) -> list[str]:
        return _split_csv(value)

    @field_validator("target_ips")
    @classmethod
    def validate_target_ips(cls, value: tuple[IPv4Address, ...]) -> tuple[IPv4Address, ...]:
        if not value:
            raise ValueError("At least one target IPv4 address must be configured.")

        try:
            normalized = tuple(TargetIP.from_raw(item).value for item in value)
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc
        if len(set(normalized)) != len(normalized):
            raise ValueError("Target IPv4 addresses must be unique.")

        return normalized

    @field_validator("dnsbl_providers", mode="before")
    @classmethod
    def parse_dnsbl_providers(cls, value: object) -> list[str]:
        return _split_csv(value)

    @field_validator("dnsbl_providers")
    @classmethod
    def validate_dnsbl_providers(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("At least one DNSBL provider must be configured.")

        try:
            normalized = tuple(DnsblProvider.from_raw(item).name for item in value)
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc
        if len(set(normalized)) != len(normalized):
            raise ValueError("DNSBL providers must be unique.")

        return normalized

    @field_validator(
        "telegram_bot_token",
        "telegram_chat_id",
        "discord_webhook_url",
        "host_label",
        mode="before",
    )
    @classmethod
    def normalize_optional_credentials(cls, value: object) -> object:
        return _blank_to_none(value)

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout_seconds(cls, value: int) -> int:
        if not MIN_TIMEOUT_SECONDS <= value <= MAX_TIMEOUT_SECONDS:
            raise ValueError(
                f"MAIL_RBL_MONITOR_TIMEOUT_SECONDS must be between "
                f"{MIN_TIMEOUT_SECONDS} and {MAX_TIMEOUT_SECONDS}."
            )
        return value

    @model_validator(mode="after")
    def validate_notifier_credentials(self) -> Self:
        if self.enable_telegram and (
            self.telegram_bot_token is None or self.telegram_chat_id is None
        ):
            raise ValueError(
                "Telegram credentials are required when MAIL_RBL_MONITOR_ENABLE_TELEGRAM=true."
            )

        if self.enable_discord and self.discord_webhook_url is None:
            raise ValueError(
                "Discord webhook URL is required when MAIL_RBL_MONITOR_ENABLE_DISCORD=true."
            )

        return self

    def apply_cli_overrides(self, *, dry_run: bool) -> Settings:
        return self.model_validate({**self.model_dump(), "dry_run": dry_run})

    def to_runtime_summary(self) -> AppRuntimeConfigSummary:
        return build_runtime_summary(
            environment=self.app_env,
            log_level=self.app_log_level,
            timeout_seconds=self.timeout_seconds,
            dry_run=self.dry_run,
            target_ips=tuple(TargetIP.from_raw(item) for item in self.target_ips),
            providers=tuple(DnsblProvider.from_raw(item) for item in self.dnsbl_providers),
            telegram_enabled=self.enable_telegram,
            discord_enabled=self.enable_discord,
            alert_context=OperatorAlertContext(
                host_label=self.host_label,
                include_hostname_in_alerts=self.include_hostname_in_alerts,
                include_environment_in_alerts=self.include_environment_in_alerts,
                include_utc_timestamp_in_alerts=self.include_utc_timestamp_in_alerts,
            ),
        )


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise ConfigurationError(f"Invalid configuration: {details}") from exc
    except SettingsError as exc:
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc


if TYPE_CHECKING:
    from mail_rbl_monitor.domain.models import AppRuntimeConfigSummary
