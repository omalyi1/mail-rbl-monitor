# Local Development

## Prerequisites

- `uv`
- Python 3.12 or newer

If Python 3.12 is not already available locally:

```bash
uv python install 3.12
```

## Setup

```bash
uv sync --group dev
cp .env.example .env
```

Edit `.env` with the target IPv4 addresses and DNSBL providers you want to monitor. Leave `MAIL_RBL_MONITOR_DRY_RUN=true` while validating configuration locally, then switch it to `false` when you want to exercise the real DNS and notification path.

Optional alert context settings are also available:

- `MAIL_RBL_MONITOR_HOST_LABEL`
- `MAIL_RBL_MONITOR_INCLUDE_HOSTNAME_IN_ALERTS`
- `MAIL_RBL_MONITOR_INCLUDE_ENVIRONMENT_IN_ALERTS`
- `MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS`

## Day-to-day commands

Run the dry-run bootstrap flow:

```bash
uv run mail-rbl-monitor --dry-run
```

Run the real monitoring flow:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor
```

Run the dry-run JSON flow:

```bash
uv run mail-rbl-monitor --dry-run --json
```

Run the real monitoring flow with JSON output:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false uv run mail-rbl-monitor --json
```

Run tests:

```bash
uv run pytest
```

Run lint and formatting checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Helper scripts are also available:

```bash
./scripts/run-check.sh --dry-run
./scripts/test.sh
```

Example real run with explicit env overrides:

```bash
MAIL_RBL_MONITOR_DRY_RUN=false \
MAIL_RBL_MONITOR_TARGET_IPS=136.243.71.222 \
MAIL_RBL_MONITOR_DNSBL_PROVIDERS=zen.spamhaus.org,bl.spamcop.net \
uv run mail-rbl-monitor
```

## Development expectations

- keep application logic out of the CLI layer
- keep infrastructure behavior behind typed ports
- avoid introducing stateful infrastructure until a concrete requirement exists
- keep tests deterministic and free of live network calls
- prefer mocking DNS and HTTP boundaries instead of monkeypatching domain logic
- keep JSON serialization at the presentation boundary rather than mixing it into DNS or notifier adapters
