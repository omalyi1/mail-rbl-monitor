# mail-rbl-monitor

`mail-rbl-monitor` is a lightweight Python service for checking whether configured mail server IPv4 addresses appear in DNS-based block lists (DNSBL/RBL providers). The service is intentionally built as a deterministic one-shot command so it can be triggered later by `cron` or a `systemd` timer without embedding a scheduler into the application itself.

This project prefers DNSBL lookups over paid REST wrappers because DNSBLs are natively queried through DNS, which keeps the check path transparent, avoids needless vendor lock-in, and keeps the runtime surface small. Future phases will still need to respect each provider's acceptable-use and query-volume requirements.

## Phase 1 scope

Phase 1 delivers the production-grade repository foundation only:

- `uv`-based Python 3.12+ workflow
- `src/` package layout with layered boundaries
- typed env-driven settings using Pydantic v2
- structured logging
- domain models, exceptions, and ports for DNS resolution and notifications
- a one-shot CLI bootstrap flow with dry-run behavior
- deterministic tests, docs, scripts, and Cursor rules

No real DNSBL queries, persistence, retries, scheduler, or outbound Telegram/Discord traffic are implemented yet.

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

## Dry-run behavior

Phase 1 only validates configuration, initializes logging, logs a startup summary, and exits successfully:

```bash
uv run python -m mail_rbl_monitor --dry-run
```

Expected outcome:

- configuration is loaded from environment variables or `.env`
- IPv4 targets and provider names are validated
- notifier credentials are validated only when a channel is enabled
- startup context is logged without exposing secrets

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

Phase 2 should add real DNSBL provider query logic behind the existing interfaces, plus notification delivery adapters for Telegram and Discord. Persistence, alert deduplication, and richer operations tooling remain intentionally deferred until a concrete requirement justifies them.
