# mail-rbl-monitor

`mail-rbl-monitor` is a lightweight Python service for checking whether configured mail server IPv4 addresses appear in DNS-based block lists (DNSBL/RBL providers). The service stays intentionally deterministic and one-shot so it fits cleanly under `cron`, `systemd` timers, CI jobs, or other external schedulers.

This project prefers DNSBL lookups over paid REST wrappers because DNSBLs are queried natively through DNS. That keeps the check path transparent, avoids vendor lock-in, and keeps the runtime surface small. The application performs direct DNS queries rather than website scraping or browser automation.

## Phase 4 scope

Phase 4 finishes the production-readiness pass on top of the existing monitoring flow:

- `uv`-based Python 3.12+ workflow
- `src/` package layout with layered boundaries
- typed env-driven settings using Pydantic v2
- structured logging
- real DNSBL A/TXT lookups with `dnspython`
- real Telegram and Discord delivery adapters with `httpx`
- provider-driven results for clean, listed, and provider-error states
- stable `--json` output for schedulers and scripts
- concise alert context with environment, host, and UTC timestamp controls
- structured notification failure accounting
- secret-safe operator-facing failure output
- production env examples, runbooks, systemd docs, and release checklist
- minimal GitHub Actions CI quality gate
- systemd templates, docs, scripts, and tests aligned with production use

Still intentionally deferred: retries, persistence, deduplication, scheduler logic inside Python, and any API or UI surface.

## Quickstart

```bash
uv sync --group dev
cp .env.example .env
uv run mail-rbl-monitor --dry-run
```

For production-oriented deployments, start from [.env.prod.example](/home/om/projects/golos/.env.prod.example) instead of `.env.example`.

Useful commands:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run mail-rbl-monitor --help
```

## How DNSBL detection works

For each configured target IPv4 address and provider:

1. Reverse the IPv4 octets and append the provider domain.
2. Query the resulting DNS name for `A` records.
3. If one or more `A` records are returned, classify the target as `listed`.
4. If the provider returns `NXDOMAIN`, classify the target as `clean`.
5. If the provider times out, returns `NoAnswer`, loses nameserver availability, or otherwise fails to answer cleanly, classify the provider check as `error`.
6. If listed, attempt a best-effort `TXT` lookup for human-readable detail.

Provider failures are never silently treated as clean.

## Provider metadata

The in-repo provider catalog intentionally stays small. It currently seeds metadata for:

- `zen.spamhaus.org`
- `b.barracudacentral.org`
- `bl.spamcop.net`

Known providers expose human-facing metadata such as display names, TXT support hints, and reference URLs. Unknown but valid provider domains are still accepted safely with sensible defaults.

## Dry-run, real run, and JSON mode

Dry-run validates configuration, initializes logging, logs the startup summary, and exits without DNS or HTTP side effects:

```bash
uv run mail-rbl-monitor --dry-run
```

Real run performs DNSBL checks and sends notifications only if at least one listing is found:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor
```

Machine-readable JSON output is available in both modes:

```bash
uv run mail-rbl-monitor --dry-run --json
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor --json
```

`--json` writes one stable compact JSON document to stdout. Logs still go to stderr. Secrets are never included in the JSON payload.

When a notification failure occurs, the JSON failure payload now includes operator-safe delivery context such as:

- `stage`
- `failed_channel`
- `attempted_notification_channels`
- `notifications_sent_before_failure`

## Alert context settings

- `MAIL_RBL_MONITOR_HOST_LABEL`: optional operator-facing label such as `mail-01`
- `MAIL_RBL_MONITOR_INCLUDE_HOSTNAME_IN_ALERTS`: include the configured host label, or fall back to the system hostname when no label is set
- `MAIL_RBL_MONITOR_INCLUDE_ENVIRONMENT_IN_ALERTS`: include `APP_ENV` in alert text
- `MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS`: include the UTC run timestamp in alert text

These settings affect alert formatting and JSON context only. They do not change DNS or notifier behavior.

## Notification behavior

- If one or more listings are found, the service formats a single plain-text alert message for the run.
- The alert is delivered through enabled Telegram and or Discord adapters.
- No success notification is sent when everything is clean.
- Provider errors alone do not trigger notifications in this phase.
- If a listing is found and notification delivery fails, the run exits with `1` and reports which channels were attempted, which succeeded before failure, and which channel failed.

## Exit codes

- `0`: completed successfully, no listings found
- `20`: completed successfully, one or more listings found
- `30`: completed successfully, no listings found, but one or more provider checks failed
- `1`: invalid configuration or unrecoverable application error

If a run has both listings and provider errors, the process exits with `20`.

## Example commands

Dry-run human mode:

```bash
uv run mail-rbl-monitor --dry-run
```

Real run human mode:

```bash
uv run mail-rbl-monitor
```

Dry-run JSON mode:

```bash
uv run mail-rbl-monitor --dry-run --json
```

Real run JSON mode:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor --json
```

Real run with env overrides:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false \
MAIL_RBL_MONITOR_TARGET_IPS=136.243.71.222 \
MAIL_RBL_MONITOR_DNSBL_PROVIDERS=zen.spamhaus.org,bl.spamcop.net \
uv run mail-rbl-monitor
```

## Project layout

```text
.
├── .cursor/rules/
├── deploy/systemd/
├── docs/
├── scripts/
├── src/mail_rbl_monitor/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── presentation/
└── tests/
```

See [docs/architecture.md](docs/architecture.md), [docs/local-development.md](docs/local-development.md), and [docs/operations.md](docs/operations.md) for the operational and architectural details.

Additional operator assets:

- [docs/runbook.md](docs/runbook.md)
- [docs/security.md](docs/security.md)
- [docs/release-checklist.md](docs/release-checklist.md)
- [deploy/systemd/README.md](deploy/systemd/README.md)

The repository also includes a minimal CI quality gate in [.github/workflows/ci.yml](/home/om/projects/golos/.github/workflows/ci.yml).

## Next planned phase

The next phase can consider narrowly justified improvements such as limited retry policy, more provider metadata, or optional alert deduplication only if concrete operational requirements appear. Persistence, long-running scheduling, and broader monitoring-platform behavior remain intentionally out of scope.
