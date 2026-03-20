# Operations

## Intended runtime model

This service is meant to run as a one-shot command under an external scheduler, not as a daemon with an internal loop.

Typical future execution models:

- `cron` on a small Linux host
- `systemd` service plus `systemd` timer
- a lightweight job runner in CI or a VM

Example future invocation:

```bash
uv run python -m mail_rbl_monitor
```

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
- non-zero exits should be treated as configuration or runtime failures by the outer scheduler

## High-level failure modes

- invalid environment configuration, such as malformed IPv4 addresses or missing notifier credentials
- unsupported or malformed DNSBL provider names
- future provider resolution failures when DNS lookups are implemented
- future notifier delivery failures when outbound adapters are implemented

The surrounding scheduler should capture stderr/stdout, surface non-zero exit codes, and alert if repeated failures occur.
