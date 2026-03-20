# Architecture

## Why a one-shot CLI

This service is designed as a deterministic one-shot command instead of a long-running worker. That keeps execution simple, makes failures easy to reason about, and pairs naturally with `cron` or `systemd` timers. The application starts, validates configuration, performs its work, emits logs or JSON output, and exits.

That shape remains the right fit in Phase 4 because the workflow is still bounded and deterministic: load config, perform DNSBL checks, optionally send notifications, emit operator-facing output, and exit.

## Layered boundaries

The repository uses a small layered architecture:

- `domain/`: business vocabulary, value objects, enums, exceptions, and ports
- `application/`: one-shot orchestration and alert formatting
- `infrastructure/`: adapters for DNS resolution, provider metadata, and notification delivery
- `presentation/`: serialization and presentation-facing helpers
- `cli.py`: process entrypoint, argument parsing, and exit behavior

The domain layer does not know about shell invocation, environment parsing, or transport formats. Infrastructure adapters sit behind ports so DNS and notification behavior remain testable without live network access.

JSON output belongs at the CLI and presentation boundary. The application returns typed run models, while serialization happens outside the DNS and notifier adapters so transport concerns do not leak into the core workflow.

## Configuration and context flow

Configuration enters through `mail_rbl_monitor.config.Settings`, which reads environment variables and optional `.env` values using `pydantic-settings`.

The settings layer is responsible for:

- parsing comma-separated IPv4 targets and DNSBL provider names
- validating timeout bounds
- enforcing notifier credential requirements only when a notifier is enabled
- carrying a small operator context surface for alerts
- converting validated settings into a domain-facing runtime summary

Phase 3 adds controlled operator context:

- optional host label
- optional hostname fallback inclusion
- optional environment inclusion in alerts
- optional UTC timestamp inclusion in alerts

This context is resolved once for each run, then propagated through the run summary so human alerts and JSON output describe the same execution.

Secrets are never logged or serialized. Phase 4 adds explicit secret redaction at operator-facing failure boundaries so JSON output and failure logs remain safe even if an upstream error message includes a configured token or webhook URL.

## Execution flow

The main execution path lives in `application/run_check.py`:

1. Build a safe runtime summary from validated settings.
2. Generate one UTC run timestamp and resolve the effective host label for the run.
3. If `dry_run` is enabled, log startup information and exit without DNS or HTTP calls.
4. Otherwise, iterate through each configured target IP and provider.
5. Build the DNSBL query name by reversing the IPv4 octets and appending the provider domain.
6. Use the DNS adapter to classify the result as `clean`, `listed`, or `error`.
7. Aggregate provider results into target-level and run-level summaries.
8. If listings are present, format a single plain-text alert and send it through enabled notification adapters.
9. If notification delivery fails, treat the run as failed instead of pretending the alert was delivered successfully.
10. Return a structured run summary that the CLI can map to exit codes and optional JSON output.

## DNS and provider behavior

The DNS adapter uses `dnspython` directly:

- `A` answer with one or more records means the target is listed
- `NXDOMAIN` means the target is clean for that provider
- TXT lookups are best-effort and only attempted after a positive listing
- provider failures are never silently treated as clean

Provider failure classification stays intentionally small and operationally useful:

- `timeout`
- `no_answer`
- `no_nameservers`
- `dns_exception`
- `unexpected`

That is enough to explain degraded coverage in logs, JSON output, and operator workflows without building a large taxonomy.

## Provider catalog

The provider catalog is intentionally small and in-repo. It seeds metadata for common providers without turning provider handling into a framework.

Known metadata currently includes:

- display name
- TXT support hint
- reference URL for seeded providers

Unknown but valid provider domains still flow through the system safely with sensible defaults.

## Presentation outputs

The service now exposes two operator-facing output styles:

- structured logs on stderr for humans and service managers
- stable JSON on stdout when `--json` is requested

This split keeps logs useful for day-to-day inspection while giving `cron`, `systemd`, CI, and wrapper scripts a stable machine-readable contract.

Notification failure remains fatal by design. If a listing is found but the alert path fails, the service exits with `1` because operators should never interpret that run as fully successful. Phase 4 adds explicit notification failure accounting so partial delivery is visible without weakening that failure contract.

## Extensibility path

The structure is ready for further targeted improvements:

- add more provider metadata when real operational need appears
- add limited retry behavior only if DNS or notification failure patterns justify it
- add optional deduplication or audit state only if a concrete requirement appears

The repository is intentionally not shaped as a generic monitoring platform. It is a focused mail reputation check service with deterministic execution.
