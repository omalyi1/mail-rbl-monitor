# mail-rbl-monitor

`mail-rbl-monitor` is a lightweight Python service for checking whether configured mail server IPv4 addresses appear in DNS-based block lists (DNSBL/RBL providers). The service is intentionally built as a deterministic one-shot command so it can be triggered later by `cron` or a `systemd` timer without embedding a scheduler into the application itself.

This project prefers DNSBL lookups over paid REST wrappers because DNSBLs are natively queried through DNS, which keeps the check path transparent, avoids needless vendor lock-in, and keeps the runtime surface small. The application performs direct DNS queries instead of website scraping or browser automation.

## Phase 2 scope

Phase 2 delivers the real monitoring flow on top of the Phase 1 foundation:

- `uv`-based Python 3.12+ workflow
- `src/` package layout with layered boundaries
- typed env-driven settings using Pydantic v2
- structured logging
- real DNSBL A/TXT lookups with `dnspython`
- real Telegram and Discord delivery adapters with `httpx`
- provider-driven results for clean, listed, and provider-error states
- deterministic dry-run behavior with no DNS or HTTP side effects
- deterministic tests, docs, scripts, and Cursor rules

Still intentionally deferred: retries, persistence, deduplication, scheduler logic, and any API/UI surface.

## Quickstart

```bash
uv sync --group dev
cp .env.example .env
uv run python -m mail_rbl_monitor --dry-run
```

Useful commands:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python -m mail_rbl_monitor --help
```

## How DNSBL detection works

For each configured target IPv4 address and provider:

1. Reverse the IPv4 octets and append the provider domain.
2. Query the resulting DNS name for `A` records.
3. If one or more `A` records are returned, classify the target as `listed`.
4. If the provider returns `NXDOMAIN`, classify the target as `clean`.
5. If the provider times out, returns `NoAnswer`, or otherwise fails to answer cleanly, classify the provider check as `error`.
6. If listed, attempt a best-effort `TXT` lookup for human-readable detail.

Provider errors are not silently treated as clean.

## Supported provider examples

The in-repo provider catalog currently seeds metadata for:

- `zen.spamhaus.org`
- `b.barracudacentral.org`
- `bl.spamcop.net`

The service still accepts other syntactically valid DNSBL provider domains, but only the seeded providers currently have explicit catalog metadata.

## Dry-run vs real run

Dry-run validates configuration, initializes logging, logs the startup summary, and exits without performing DNS or HTTP side effects:

```bash
uv run python -m mail_rbl_monitor --dry-run
```

Real run performs DNSBL checks and sends notifications only if at least one listing is found:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false uv run python -m mail_rbl_monitor
```

## Notification behavior

- If one or more listings are found, the service formats a single plain-text alert message for the run.
- The alert is delivered through enabled Telegram and/or Discord adapters.
- No success notification is sent when everything is clean.
- Provider errors alone do not trigger notifications in this phase.

## Exit codes

- `0`: completed successfully, no listings found
- `20`: completed successfully, one or more listings found
- `30`: completed successfully, no listings found, but one or more provider checks failed
- `1`: invalid configuration or unrecoverable application error

If a run has both listings and provider errors, the process exits with `20`.

## Example commands

Dry-run:

```bash
uv run python -m mail_rbl_monitor --dry-run
```

Real run with `.env`:

```bash
uv run python -m mail_rbl_monitor
```

Real run with env overrides:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false \
MAIL_RBL_MONITOR_TARGET_IPS=136.243.71.222 \
MAIL_RBL_MONITOR_DNSBL_PROVIDERS=zen.spamhaus.org,bl.spamcop.net \
uv run python -m mail_rbl_monitor
```

## Project layout

```text
.
├── .cursor/rules/
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

## Next planned phase

Phase 3 can focus on operational hardening such as controlled retries, richer provider coverage, and optional deduplication only if a concrete requirement justifies it. Persistence, long-running scheduling, and broader monitoring-platform behavior remain intentionally out of scope.
