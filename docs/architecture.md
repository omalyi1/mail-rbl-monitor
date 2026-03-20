# Architecture

## Why a one-shot CLI

This service is designed as a deterministic one-shot command instead of a long-running worker. That keeps execution simple, makes failures easy to reason about, and pairs naturally with `cron` or `systemd` timers. The application starts, validates configuration, performs its work, emits logs, and exits.

That shape remains a better fit in Phase 2 because the real monitoring workflow is still bounded and deterministic: load config, perform DNSBL checks, optionally send notifications, and exit.

## Layered boundaries

The repository uses a small layered architecture:

- `domain/`: pure business vocabulary, value objects, enums, exceptions, and ports
- `application/`: one-shot orchestration for the check workflow and alert formatting
- `infrastructure/`: adapters for DNS resolution, provider metadata, and notification delivery
- `presentation/`: reserved for future user-facing surfaces without leaking them into the core
- `cli.py`: process entrypoint and argument parsing

The domain layer does not know about logging configuration, shell invocation, or environment parsing. Infrastructure adapters sit behind ports so DNS lookups and notifier delivery remain testable without live network access.

## Configuration flow

Configuration enters through `mail_rbl_monitor.config.Settings`, which reads environment variables and optional `.env` values using `pydantic-settings`.

The settings layer is responsible for:

- parsing comma-separated IPv4 targets and DNSBL provider names
- validating timeout bounds
- enforcing notifier credential requirements only when a notifier is enabled
- converting validated settings into a domain-facing runtime summary

Secrets are never logged. The runtime summary only includes safe operational context such as counts, enabled channels, and configured targets/providers.

## Phase 2 execution flow

The main execution path lives in `application/run_check.py`:

1. Build a safe runtime summary from validated settings.
2. If `dry_run` is enabled, log startup information and exit without DNS or HTTP calls.
3. Otherwise, iterate through each configured target IP and provider.
4. Build the DNSBL query name by reversing the IPv4 octets and appending the provider domain.
5. Use the DNS adapter to classify the result as `clean`, `listed`, or `error`.
6. Aggregate provider results into target-level and run-level summaries.
7. If listings are present, format a single plain-text alert and send it through enabled notification adapters.

## DNS and provider behavior

The DNS adapter uses `dnspython` directly:

- `A` answer with one or more records means the target is listed
- `NXDOMAIN` means the target is clean for that provider
- timeout, nameserver failures, and other DNS failures are provider errors
- `NoAnswer` is deliberately treated as a provider error rather than silently downgraded to clean
- TXT lookups are best-effort and only attempted after a positive listing

The provider catalog is intentionally small and in-repo. It seeds metadata for common providers without turning provider handling into a framework.

## Extensibility path

The structure is ready for further targeted improvements:

- add more provider metadata when real operational need appears
- add limited retry behavior only if DNS or notification failure patterns justify it
- add optional deduplication or audit state only if a concrete requirement appears

The repository is intentionally not shaped as a generic monitoring platform. It is a focused mail reputation check service with deterministic execution.
