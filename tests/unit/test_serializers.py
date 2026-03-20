from mail_rbl_monitor.constants import ExitCode
from mail_rbl_monitor.domain.enums import (
    AppEnvironment,
    ListingStatus,
    NotificationChannel,
    ProviderErrorKind,
)
from mail_rbl_monitor.domain.models import (
    AppRuntimeConfigSummary,
    DnsblProvider,
    OperatorAlertContext,
    ProviderCheckResult,
    RunSummary,
    TargetCheckResult,
    TargetIP,
)
from mail_rbl_monitor.presentation.serializers import serialize_failure, serialize_run_summary


def _build_runtime_config(*, dry_run: bool) -> AppRuntimeConfigSummary:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    return AppRuntimeConfigSummary(
        environment=AppEnvironment.PROD,
        log_level="INFO",
        timeout_seconds=5,
        dry_run=dry_run,
        target_ips=(target_ip,),
        providers=(provider,),
        telegram_enabled=True,
        discord_enabled=False,
        enabled_channels=(NotificationChannel.TELEGRAM,),
        alert_context=OperatorAlertContext(
            host_label="mail-01",
            include_hostname_in_alerts=True,
            include_environment_in_alerts=True,
            include_utc_timestamp_in_alerts=True,
        ),
    )


def _build_provider_result(
    *,
    status: ListingStatus,
    error_kind: ProviderErrorKind | None = None,
) -> ProviderCheckResult:
    target_ip = TargetIP.from_raw("136.243.71.222")
    provider = DnsblProvider.from_raw("zen.spamhaus.org")
    return ProviderCheckResult(
        target_ip=target_ip,
        provider=provider,
        query_name="222.71.243.136.zen.spamhaus.org",
        status=status,
        listed_addresses=("127.0.0.2",) if status == ListingStatus.LISTED else (),
        txt_reasons=("Spamhaus listed",) if status == ListingStatus.LISTED else (),
        error_message="DNS query timed out." if status == ListingStatus.ERROR else None,
        error_kind=error_kind,
        latency_ms=12,
    )


def test_serialize_run_summary_dry_run_shape() -> None:
    run_summary = RunSummary(
        runtime_config=_build_runtime_config(dry_run=True),
        checked_at_utc="2026-03-20T09:00:00Z",
        host_label="mail-01",
    )

    payload = serialize_run_summary(run_summary, exit_code=int(ExitCode.SUCCESS))
    summary = payload["summary"]

    assert payload["dry_run"] is True
    assert payload["host_label"] == "mail-01"
    assert summary is not None
    assert summary["total_provider_checks"] == 0
    assert payload["results"] == []


def test_serialize_run_summary_clean_real_run_shape() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    run_summary = RunSummary(
        runtime_config=_build_runtime_config(dry_run=False),
        checked_at_utc="2026-03-20T09:00:00Z",
        host_label="mail-01",
        target_results=(
            TargetCheckResult(
                target_ip=target_ip,
                provider_results=(_build_provider_result(status=ListingStatus.CLEAN),),
            ),
        ),
    )

    payload = serialize_run_summary(run_summary, exit_code=int(ExitCode.SUCCESS))
    summary = payload["summary"]

    assert payload["dry_run"] is False
    assert summary is not None
    assert summary["listed_count"] == 0
    assert summary["error_count"] == 0
    assert payload["results"][0]["provider_results"][0]["status"] == "clean"


def test_serialize_run_summary_listing_found_shape() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    run_summary = RunSummary(
        runtime_config=_build_runtime_config(dry_run=False),
        checked_at_utc="2026-03-20T09:00:00Z",
        host_label="mail-01",
        target_results=(
            TargetCheckResult(
                target_ip=target_ip,
                provider_results=(_build_provider_result(status=ListingStatus.LISTED),),
            ),
        ),
        notifications_sent=(NotificationChannel.TELEGRAM,),
    )

    payload = serialize_run_summary(run_summary, exit_code=int(ExitCode.LISTING_FOUND))
    summary = payload["summary"]

    assert payload["exit_code"] == 20
    assert summary is not None
    assert summary["listed_count"] == 1
    assert summary["notifications_sent"] == ["telegram"]
    assert payload["results"][0]["provider_results"][0]["provider_display_name"] == "Spamhaus ZEN"


def test_serialize_run_summary_provider_error_shape() -> None:
    target_ip = TargetIP.from_raw("136.243.71.222")
    run_summary = RunSummary(
        runtime_config=_build_runtime_config(dry_run=False),
        checked_at_utc="2026-03-20T09:00:00Z",
        host_label="mail-01",
        target_results=(
            TargetCheckResult(
                target_ip=target_ip,
                provider_results=(
                    _build_provider_result(
                        status=ListingStatus.ERROR,
                        error_kind=ProviderErrorKind.TIMEOUT,
                    ),
                ),
            ),
        ),
    )

    payload = serialize_run_summary(run_summary, exit_code=int(ExitCode.PROVIDER_ERRORS))
    summary = payload["summary"]

    assert payload["exit_code"] == 30
    assert summary is not None
    assert summary["error_count"] == 1
    assert payload["results"][0]["provider_results"][0]["status"] == "error"
    assert payload["results"][0]["provider_results"][0]["error_kind"] == "timeout"


def test_serialize_failure_includes_notification_failure_fields() -> None:
    payload = serialize_failure(
        exit_code=int(ExitCode.FAILURE),
        error_type="notification_error",
        error_message="Discord notification delivery failed.",
        checked_at_utc="2026-03-20T09:00:00Z",
        environment="prod",
        dry_run=False,
        host_label="mail-01",
        targets=["136.243.71.222"],
        providers=["zen.spamhaus.org"],
        stage="notification",
        failed_channel=NotificationChannel.DISCORD,
        attempted_notification_channels=(
            NotificationChannel.TELEGRAM,
            NotificationChannel.DISCORD,
        ),
        notifications_sent_before_failure=(NotificationChannel.TELEGRAM,),
    )

    error = payload["error"]

    assert error is not None
    assert error["type"] == "notification_error"
    assert error["stage"] == "notification"
    assert error["failed_channel"] == "discord"
    assert error["attempted_notification_channels"] == ["telegram", "discord"]
    assert error["notifications_sent_before_failure"] == ["telegram"]
