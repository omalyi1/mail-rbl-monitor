# Local Development

## Prerequisites

- Python 3.12 or newer
- `uv`

If Python 3.12 is not already installed locally:

```bash
uv python install 3.12
```

## Setup

```bash
uv sync --group dev
cp .env.example .env
```

Edit `.env` with the target IPv4 addresses and provider domains you want to monitor.
Keep `MAIL_RBL_MONITOR_DRY_RUN=true` while validating configuration locally.

For production-oriented examples, start from [`.env.prod.example`](../.env.prod.example).

## Validation workflow

Dry-run is the canonical validation path:

```bash
uv run mail-rbl-monitor --dry-run
```

Dry-run JSON validation:

```bash
uv run mail-rbl-monitor --dry-run --json
```

## Real run examples

Human-readable real run:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor
```

JSON real run:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor --json
```

Example run with explicit env overrides:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false \
MAIL_RBL_MONITOR_TARGET_IPS=136.243.71.222 \
MAIL_RBL_MONITOR_DNSBL_PROVIDERS=zen.spamhaus.org,bl.spamcop.net \
uv run mail-rbl-monitor
```

## Alert presentation settings

- `MAIL_RBL_MONITOR_HOST_LABEL`
- `MAIL_RBL_MONITOR_INCLUDE_HOSTNAME_IN_ALERTS`
- `MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS`
- `MAIL_RBL_MONITOR_ALERT_TIMEZONE`

`MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS` is still accepted as a deprecated
compatibility alias for the checked-at setting.

## Quality checks

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

## Safe local notifier testing

- use `--dry-run` with placeholder notifier credentials to validate configuration without
  DNS or HTTP side effects
- do not use real production notifier secrets in a committed `.env`
- if you need a live notifier test, use temporary credentials pointed at a test chat or
  webhook and run it manually

## Contributor expectations

- keep the one-shot CLI architecture intact unless a change is discussed explicitly
- keep infrastructure behavior behind typed ports
- keep tests deterministic and free of live network calls
- keep docs aligned with code and actual commands
