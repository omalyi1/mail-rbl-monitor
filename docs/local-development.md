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

Edit `.env` with the target IPv4 addresses and DNSBL providers you want to monitor.

## Day-to-day commands

Run the dry-run bootstrap flow:

```bash
uv run python -m mail_rbl_monitor --dry-run
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

## Development expectations

- keep application logic out of the CLI layer
- keep infrastructure behavior behind typed ports
- avoid introducing stateful infrastructure until a concrete requirement exists
- keep tests deterministic and free of live network calls
