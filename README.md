# mail-rbl-monitor

`mail-rbl-monitor` is a small Python service that checks configured mail server IPv4
addresses against DNS-based block lists (DNSBL/RBL providers) and sends alerts when a
listing is detected. It is intentionally designed as a deterministic one-shot CLI so it
fits cleanly under `cron`, `systemd` timers, CI jobs, or other external schedulers.

## What the service does

For each configured target IPv4 address and DNSBL provider, the service:

1. Builds the provider query name by reversing the IPv4 octets and appending the
   provider domain.
2. Performs a real DNS `A` lookup with `dnspython`.
3. Classifies the result as `clean`, `listed`, or `error`.
4. Attempts a best-effort DNS `TXT` lookup when a listing is found.
5. Sends one alert message through the enabled Telegram and/or Discord channels when any
   listing is detected.

The runtime stays small and explicit:

- one-shot command, not a daemon
- no database or local state
- no in-process scheduler
- no retries or deduplication
- no web API or web UI

## Why DNSBL queries instead of paid web APIs

DNSBL providers are DNS-native systems. Querying them through DNS keeps the monitoring
path simple, transparent, and easy to audit.

This project prefers direct DNS queries because they:

- avoid extra REST wrappers for a DNS problem
- reduce runtime dependencies and vendor lock-in
- stay easy to test without browser automation or website scraping
- map directly to how DNSBL providers are actually consumed

## Key features

- Python 3.12+ with `uv` and a `src/` layout
- typed settings with `pydantic-settings`
- real DNSBL lookups with `dnspython`
- real Telegram and Discord delivery with sync `httpx`
- stable `--json` output for wrappers and schedulers
- structured provider error classification
- secret-safe operator-facing error handling
- systemd templates and operator docs
- pytest, ruff, mypy, and a minimal GitHub Actions CI workflow

## Quickstart

```bash
uv sync --group dev
cp .env.example .env
```

Edit `.env` with at least one target IPv4 address and one provider, then validate the
config:

```bash
uv run mail-rbl-monitor --dry-run
```

For production-oriented deployments, start from
[`.env.prod.example`](.env.prod.example).

## Configuration overview

The service is configured entirely through environment variables.

Core settings:

- `APP_ENV`
- `APP_LOG_LEVEL`
- `MAIL_RBL_MONITOR_TARGET_IPS`
- `MAIL_RBL_MONITOR_DNSBL_PROVIDERS`
- `MAIL_RBL_MONITOR_TIMEOUT_SECONDS`
- `MAIL_RBL_MONITOR_DRY_RUN`

Notifier settings:

- `MAIL_RBL_MONITOR_ENABLE_TELEGRAM`
- `MAIL_RBL_MONITOR_TELEGRAM_BOT_TOKEN`
- `MAIL_RBL_MONITOR_TELEGRAM_CHAT_ID`
- `MAIL_RBL_MONITOR_ENABLE_DISCORD`
- `MAIL_RBL_MONITOR_DISCORD_WEBHOOK_URL`

Alert context settings:

- `MAIL_RBL_MONITOR_HOST_LABEL`
- `MAIL_RBL_MONITOR_INCLUDE_HOSTNAME_IN_ALERTS`
- `MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS`
- `MAIL_RBL_MONITOR_ALERT_TIMEZONE`

`MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS` is the canonical public setting.
The older `MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS` name is still accepted as
a backward-compatible alias and is documented as deprecated.

The alert timezone uses an IANA timezone such as `Europe/Kyiv`. Timezone conversion uses
the Python standard library `zoneinfo` module, so DST and seasonal offset changes are
handled automatically.

## Example alert output

```text
[mail-rbl-monitor] LISTING DETECTED
Host: mail-01
Checked at (Europe/Kyiv): 2026-03-23 12:12:02

Target IP: 136.243.71.222
Listed in:
- Spamhaus ZEN (zen.spamhaus.org) (A: 127.0.0.2; TXT: Spamhaus listed)
```

## Dry-run, real-run, and JSON mode

Dry-run validates configuration and exits without DNS or HTTP side effects:

```bash
uv run mail-rbl-monitor --dry-run
```

Real run performs DNSBL checks and sends notifications only when a listing is found:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor
```

Machine-readable JSON output is available in both modes:

```bash
uv run mail-rbl-monitor --dry-run --json
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor --json
```

`--json` writes one stable JSON document to stdout while logs continue to go to stderr.
Secrets are never included in the JSON payload.

## Exit codes

- `0`: completed successfully, no listings found
- `20`: completed successfully, one or more listings found
- `30`: completed successfully, no listings found, but one or more provider checks failed
- `1`: invalid configuration or unrecoverable application failure

If a listing is detected and notification delivery fails, the run exits with `1`. The
JSON failure payload includes operator-safe context such as the failed channel, attempted
channels, and channels that succeeded before failure.

## Deployment options

Recommended deployment shapes:

- `cron` on a small Linux host
- `systemd` oneshot service plus timer
- a scheduled job runner in CI or a VM

Helpful deployment docs:

- [Systemd templates](deploy/systemd/README.md)
- [Operations guide](docs/operations.md)
- [Runbook](docs/runbook.md)
- [Security notes](docs/security.md)

## Project layout

```text
.
├── .cursor/rules/
├── .github/
├── deploy/systemd/
├── docs/
├── scripts/
├── src/mail_rbl_monitor/
└── tests/
```

Architecture details live in [docs/architecture.md](docs/architecture.md).

## Limitations and non-goals

This project intentionally does not include:

- a long-running daemon
- a database or alert history
- retries or backoff
- alert deduplication
- a metrics stack
- a web UI or API server
- container orchestration or deployment automation

## Development and quality checks

Local quality commands:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

Helper scripts are also available:

```bash
./scripts/run-check.sh --dry-run
./scripts/test.sh
```

The repository includes a minimal GitHub Actions CI workflow in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) that runs the same lint, format,
typing, and test checks.

Contribution guidance lives in [CONTRIBUTING.md](CONTRIBUTING.md), and community
standards are described in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security and responsible disclosure

For public vulnerability reporting expectations, see [SECURITY.md](SECURITY.md).
Operational deployment guidance is in [docs/security.md](docs/security.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
