# Operations

## Intended runtime model

This service is meant to run as a one-shot command under an external scheduler, not as a daemon with an internal loop.

Typical execution models:

- `cron` on a small Linux host
- `systemd` service plus `systemd` timer
- a lightweight job runner in CI or a VM

Example future invocation:

```bash
uv run mail-rbl-monitor
```

Example cron entry:

```cron
0 9 * * * cd /opt/mail-rbl-monitor && /usr/bin/env uv run mail-rbl-monitor
```

For `systemd`, keep the service one-shot and let a timer trigger it on the desired schedule. This repository includes example templates in `deploy/systemd/`:

- `deploy/systemd/mail-rbl-monitor.service`
- `deploy/systemd/mail-rbl-monitor.timer`

The service template is `Type=oneshot` and uses placeholders for the runtime user, group, working directory, and environment file. Keep the `ExecStart` command aligned with the same `uv run mail-rbl-monitor` entrypoint used locally.

## Secret handling

- keep `.env` out of version control
- inject notifier tokens and webhook URLs through environment variables
- never place Telegram bot tokens or Discord webhook URLs in docs, scripts, or source files
- rotate credentials if they are ever exposed

## Logging expectations

The application emits concise structured logs through the standard library logging stack.

Operational expectations:

- startup logs should confirm the configured targets, providers, enabled channels, and dry-run state
- when `--json` is used, stdout should contain one stable JSON document for the run
- secrets must never appear in logs
- non-zero exits should be interpreted according to the exit code contract below

## JSON output

`--json` is intended for schedulers, wrappers, and operators who want machine-readable output without parsing logs.

The JSON payload includes:

- application name and version
- environment, dry-run state, host label, and UTC timestamp
- configured targets and providers
- summary counters
- per-target and per-provider results
- notification channels actually sent
- exit code
- error information for configuration or unrecoverable application failures

JSON output does not include secrets, raw notifier credentials, or transport internals.

## Exit codes

- `0`: completed successfully, no listings found
- `20`: completed successfully, one or more listings found
- `30`: completed successfully, no listings found, but one or more provider checks failed
- `1`: invalid configuration or unrecoverable application error

If the run contains both real listings and provider errors, the process exits with `20`.

## Notification behavior

- notifications are only sent when one or more listings are detected
- the service sends a single plain-text alert message per run
- Telegram and Discord remain thin transport adapters; message formatting lives in the application layer
- provider errors alone do not trigger notifications in this phase
- if a listing is detected and notification delivery fails, the run exits with `1`

## Provider error kinds

Provider failures are classified explicitly so degraded runs are easier to interpret:

- `timeout`: the provider did not answer before the configured timeout
- `no_answer`: the provider returned no usable answer for the query
- `no_nameservers`: resolver nameservers could not answer usefully
- `dns_exception`: another `dnspython` resolver failure occurred
- `unexpected`: a non-DNS unexpected exception occurred in the resolver path

`NXDOMAIN` is not an error. It is treated as a clean result for that provider.

## High-level failure modes

- invalid environment configuration, such as malformed IPv4 addresses or missing notifier credentials
- unsupported or malformed DNSBL provider names
- provider resolution failures, such as timeouts, nameserver failures, or malformed provider responses
- notifier delivery failures when Telegram or Discord rejects a request or is unreachable

Provider errors are not silently treated as clean. If all checks are otherwise clean but one or more providers fail, the process exits with `30` so the outer scheduler can detect degraded coverage.

The surrounding scheduler should capture stderr/stdout, surface non-zero exit codes, and alert if repeated failures occur.
