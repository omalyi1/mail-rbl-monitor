from __future__ import annotations

from mail_rbl_monitor.constants import APP_NAME
from mail_rbl_monitor.domain.models import ProviderCheckResult, RunSummary
from mail_rbl_monitor.infrastructure.providers.catalog import get_provider_metadata


def format_listing_alert(run_summary: RunSummary) -> str:
    if not run_summary.has_listings:
        raise ValueError("Cannot format a listing alert for a run with no listings.")

    lines = [f"[{APP_NAME}] LISTING DETECTED"]
    context = run_summary.runtime_config.alert_context

    if context.include_environment_in_alerts:
        lines.append(f"Environment: {run_summary.runtime_config.environment.value}")
    if context.include_hostname_in_alerts and run_summary.host_label is not None:
        lines.append(f"Host: {run_summary.host_label}")
    if context.include_utc_timestamp_in_alerts:
        lines.append(f"Checked at (UTC): {run_summary.checked_at_utc}")

    if len(lines) > 1:
        lines.append("")

    for target_result in run_summary.target_results:
        if not target_result.has_listings:
            continue

        lines.extend(
            [
                "",
                f"Target IP: {target_result.target_ip}",
                "Listed in:",
            ]
        )
        lines.extend(_format_provider_result(result) for result in target_result.listed_results)

    return "\n".join(lines)


def _format_provider_result(result: ProviderCheckResult) -> str:
    provider_metadata = get_provider_metadata(result.provider)
    details: list[str] = []
    if result.listed_addresses:
        details.append(f"A: {', '.join(result.listed_addresses)}")
    if result.txt_reasons:
        details.append(f"TXT: {' | '.join(result.txt_reasons)}")

    suffix = f" ({'; '.join(details)})" if details else ""
    provider_label = provider_metadata.display_name
    if provider_label != result.provider.name:
        provider_label = f"{provider_label} ({result.provider.name})"
    return f"- {provider_label}{suffix}"
