from __future__ import annotations

import json
from typing import NotRequired, TypedDict

from mail_rbl_monitor import __version__
from mail_rbl_monitor.constants import APP_NAME
from mail_rbl_monitor.domain.enums import NotificationChannel
from mail_rbl_monitor.domain.models import ProviderCheckResult, RunSummary
from mail_rbl_monitor.infrastructure.providers.catalog import get_provider_metadata


class ProviderResultPayload(TypedDict):
    provider: str
    provider_display_name: str
    query_name: str
    provider_mode: NotRequired[str]
    status: str
    listed_addresses: list[str]
    txt_reasons: list[str]
    error_message: str | None
    error_kind: str | None
    latency_ms: int | None


class TargetResultPayload(TypedDict):
    target_ip: str
    provider_results: list[ProviderResultPayload]


class SummaryPayload(TypedDict):
    total_targets: int
    total_provider_checks: int
    listed_count: int
    error_count: int
    notifications_sent: list[str]


class FailurePayload(TypedDict):
    type: str
    message: str
    stage: NotRequired[str]
    failed_channel: NotRequired[str]
    attempted_notification_channels: NotRequired[list[str]]
    notifications_sent_before_failure: NotRequired[list[str]]


class RunPayload(TypedDict):
    app: str
    version: str
    environment: str | None
    dry_run: bool | None
    host_label: str | None
    checked_at_utc: str
    targets: list[str]
    providers: list[str]
    summary: SummaryPayload | None
    results: list[TargetResultPayload]
    exit_code: int
    error: FailurePayload | None


def serialize_run_summary(run_summary: RunSummary, *, exit_code: int) -> RunPayload:
    runtime_config = run_summary.runtime_config

    return {
        "app": APP_NAME,
        "version": __version__,
        "environment": runtime_config.environment.value,
        "dry_run": runtime_config.dry_run,
        "host_label": run_summary.host_label,
        "checked_at_utc": run_summary.checked_at_utc,
        "targets": [str(target_ip) for target_ip in runtime_config.target_ips],
        "providers": [provider.name for provider in runtime_config.providers],
        "summary": {
            "total_targets": run_summary.total_targets,
            "total_provider_checks": run_summary.total_provider_checks,
            "listed_count": run_summary.listed_count,
            "error_count": run_summary.error_count,
            "notifications_sent": [channel.value for channel in run_summary.notifications_sent],
        },
        "results": [
            {
                "target_ip": str(target_result.target_ip),
                "provider_results": [
                    _serialize_provider_result(provider_result)
                    for provider_result in target_result.provider_results
                ],
            }
            for target_result in run_summary.target_results
        ],
        "exit_code": exit_code,
        "error": None,
    }


def serialize_failure(
    *,
    exit_code: int,
    error_type: str,
    error_message: str,
    checked_at_utc: str,
    environment: str | None,
    dry_run: bool | None,
    host_label: str | None,
    targets: list[str],
    providers: list[str],
    stage: str | None = None,
    failed_channel: NotificationChannel | None = None,
    attempted_notification_channels: tuple[NotificationChannel, ...] = (),
    notifications_sent_before_failure: tuple[NotificationChannel, ...] = (),
) -> RunPayload:
    error_payload: FailurePayload = {
        "type": error_type,
        "message": error_message,
    }
    if stage is not None:
        error_payload["stage"] = stage
    if failed_channel is not None:
        error_payload["failed_channel"] = failed_channel.value
    if attempted_notification_channels:
        error_payload["attempted_notification_channels"] = [
            channel.value for channel in attempted_notification_channels
        ]
    if notifications_sent_before_failure:
        error_payload["notifications_sent_before_failure"] = [
            channel.value for channel in notifications_sent_before_failure
        ]

    return {
        "app": APP_NAME,
        "version": __version__,
        "environment": environment,
        "dry_run": dry_run,
        "host_label": host_label,
        "checked_at_utc": checked_at_utc,
        "targets": targets,
        "providers": providers,
        "summary": None,
        "results": [],
        "exit_code": exit_code,
        "error": error_payload,
    }


def _serialize_provider_result(provider_result: ProviderCheckResult) -> ProviderResultPayload:
    payload: ProviderResultPayload = {
        "provider": provider_result.provider.name,
        "provider_display_name": get_provider_metadata(provider_result.provider).display_name,
        "query_name": provider_result.query_name,
        "status": provider_result.status.value,
        "listed_addresses": list(provider_result.listed_addresses),
        "txt_reasons": list(provider_result.txt_reasons),
        "error_message": provider_result.error_message,
        "error_kind": provider_result.error_kind.value
        if provider_result.error_kind is not None
        else None,
        "latency_ms": provider_result.latency_ms,
    }
    if provider_result.provider_mode is not None:
        payload["provider_mode"] = provider_result.provider_mode.value
    return payload


def dump_json_payload(payload: RunPayload) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)
