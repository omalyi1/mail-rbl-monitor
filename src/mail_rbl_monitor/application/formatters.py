from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from mail_rbl_monitor.constants import APP_NAME
from mail_rbl_monitor.domain.models import ProviderCheckResult, RunSummary
from mail_rbl_monitor.infrastructure.providers.catalog import get_provider_metadata


def format_listing_alert(run_summary: RunSummary) -> str:
    if not run_summary.has_listings:
        raise ValueError("Cannot format a listing alert for a run with no listings.")

    lines = [f"[{APP_NAME}] LISTING DETECTED"]
    context = run_summary.runtime_config.alert_context

    if context.include_checked_at_in_alerts:
        lines.extend(
            [
                "",
                _format_checked_at_line(
                    checked_at_utc=run_summary.checked_at_utc,
                    timezone_name=context.alert_timezone,
                ),
                "",
            ]
        )
    else:
        lines.append("")

    first_target_block = True

    for target_result in run_summary.target_results:
        if not target_result.has_listings:
            continue

        if not first_target_block:
            lines.append("")

        lines.append(f"Target IP: {target_result.target_ip}")

        if context.include_hostname_in_alerts:
            target_host = context.host_for(target_result.target_ip)
            if target_host is not None:
                lines.append(f"Host: {target_host}")

        lines.append("Listed in:")
        lines.extend(_format_provider_result(result) for result in target_result.listed_results)

        first_target_block = False

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


def _format_checked_at_line(*, checked_at_utc: str, timezone_name: str) -> str:
    checked_at = datetime.fromisoformat(checked_at_utc.replace("Z", "+00:00"))
    localized = checked_at.astimezone(ZoneInfo(timezone_name))
    return f"Checked at ({timezone_name}): {localized.strftime('%Y-%m-%d %H:%M:%S')}"
