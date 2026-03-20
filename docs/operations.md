# Operations

## Intended runtime model

This service is meant to run as a one-shot command under an external scheduler, not as a daemon with an internal loop.

Typical execution models:

- `cron` on a small Linux host
- `systemd` service plus `systemd` timer
- a lightweight job runner in CI or a VM

Example future invocation:

```bash
uv run python -m mail_rbl_monitor
```

Example cron entry:

```cron
0 9 * * * cd /opt/mail-rbl-monitor && /usr/bin/env uv run python -m mail_rbl_monitor
```

For `systemd`, keep the service one-shot and let a timer trigger it on the desired schedule. The `ExecStart` command should call the same `uv run python -m mail_rbl_monitor` entrypoint used locally.

## Secret handling

- keep `.env` out of version control
- inject notifier tokens and webhook URLs through environment variables
- never place Telegram bot tokens or Discord webhook URLs in docs, scripts, or source files
- rotate credentials if they are ever exposed

## Logging expectations

The application emits concise structured logs through the standard library logging stack.

Operational expectations:

- startup logs should confirm the configured targets, providers, enabled channels, and dry-run state
- secrets must never appear in logs
- non-zero exits should be interpreted according to the exit code contract below

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

## High-level failure modes

- invalid environment configuration, such as malformed IPv4 addresses or missing notifier credentials
- unsupported or malformed DNSBL provider names
- provider resolution failures, such as timeouts, nameserver failures, or malformed provider responses
- notifier delivery failures when Telegram or Discord rejects a request or is unreachable

Provider errors are not silently treated as clean. If all checks are otherwise clean but one or more providers fail, the process exits with `30` so the outer scheduler can detect degraded coverage.

The surrounding scheduler should capture stderr/stdout, surface non-zero exit codes, and alert if repeated failures occur.
