# Architecture

## Why a one-shot CLI

`mail-rbl-monitor` is deliberately a deterministic one-shot command rather than a
long-running service. That keeps runtime behavior bounded and easy to reason about:
load configuration, perform DNSBL checks, optionally send alerts, emit logs or JSON, and
exit.

This shape stays scheduler-friendly and easy to deploy under `cron`, `systemd`, or a
simple job runner without introducing in-process scheduling or state management.

## Layered boundaries

The repository uses a small layered architecture:

- `domain/`: value objects, enums, exceptions, and ports
- `application/`: run orchestration and alert formatting
- `infrastructure/`: DNS, provider metadata, and notification adapters
- `presentation/`: JSON serialization and redaction helpers
- `cli.py`: argument parsing, process entrypoint, and exit behavior

The domain layer stays independent of shell invocation, environment parsing, and
transport formatting. DNS and notifier behavior remain behind ports so tests can stay
deterministic and free of live network calls.

## Configuration and context flow

Configuration enters through `mail_rbl_monitor.config.Settings`, which reads environment
variables and optional `.env` files through `pydantic-settings`.

The settings boundary is responsible for:

- parsing comma-separated IPv4 targets and provider domains
- validating timeout bounds
- enforcing notifier credentials only when a notifier is enabled
- accepting an optional Spamhaus DQS key without requiring provider-list changes
- validating alert presentation options such as timezone
- converting validated config into a runtime summary for the application layer

Alert context remains intentionally small:

- optional host label
- optional hostname inclusion
- optional checked-at line inclusion
- configurable IANA timezone for human-facing alert text

The canonical public env name is `MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS`. The
older `MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS` key is still accepted as a
backward-compatible alias for existing deployments.

## Execution flow

The main execution path lives in `application/run_check.py`:

1. Load and validate settings.
2. Build a runtime summary and one canonical UTC run timestamp.
3. If `dry_run` is enabled, log startup context and exit without DNS or HTTP side effects.
4. Otherwise, iterate through each target IPv4 and provider.
5. Build the DNSBL query name and perform real DNS checks through the resolver adapter.
6. Aggregate provider results into target-level and run-level summaries.
7. If listings are present, format one alert message and send it through enabled
   notifiers.
8. Return a structured run summary for exit-code selection and optional JSON output.

## DNS and provider behavior

The DNS adapter uses `dnspython` directly:

- a returned `A` answer means the target is listed
- `NXDOMAIN` means the target is clean for that provider
- `TXT` lookups are best-effort and only attempted after a positive listing
- provider failures are never silently treated as clean
- Spamhaus keeps `zen.spamhaus.org` as the canonical configured provider ID
- when `MAIL_RBL_MONITOR_SPAMHAUS_DQS_KEY` is configured, Spamhaus query routing switches
  internally to `<key>.zen.dq.spamhaus.net`
- operator-facing query names stay redacted, for example
  `222.71.243.136.<spamhaus-dqs>.zen.dq.spamhaus.net`

Provider failure classification stays intentionally small and operational:

- `timeout`
- `no_answer`
- `no_nameservers`
- `dns_exception`
- `unexpected`

## Presentation boundaries

Operator-facing output is split deliberately:

- logs go to stderr for humans and service managers
- JSON goes to stdout only when `--json` is requested

JSON serialization belongs at the presentation boundary, not inside DNS or notification
adapters. The application layer returns typed run models; the CLI decides whether to emit
human-readable logs only or a machine-readable JSON payload as well.

Notification failure remains fatal by design. If a listing is found but alert delivery
fails, the service exits with `1` rather than pretending the run succeeded.

## Secret safety

Operator-facing outputs are redacted where needed:

- secrets are never logged intentionally
- secrets are never included in JSON output
- notification failures are surfaced with stable operator-safe messages
- Spamhaus DQS keys are treated as secrets and never exposed in logs, JSON, or result
  models intended for operators

This keeps public docs, scheduler integrations, and incident workflows safer without
adding a large security abstraction layer.
