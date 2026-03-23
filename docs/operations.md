# Operations

## Intended runtime model

`mail-rbl-monitor` is meant to run as a one-shot command under an external scheduler, not
as a daemon with an internal loop.

Common execution models:

- `cron` on a Linux host
- `systemd` oneshot service plus timer
- a lightweight scheduled job runner

Example cron entry:

```cron
0 9 * * * cd /opt/mail-rbl-monitor && /usr/bin/env uv run mail-rbl-monitor
```

For `systemd`, keep the service oneshot and let the timer drive schedule frequency. This
repository includes example units in [`deploy/systemd/`](../deploy/systemd/). Installation
steps live in [`deploy/systemd/README.md`](../deploy/systemd/README.md).

## Logging and JSON output

The service emits:

- structured logs on stderr
- one stable JSON document on stdout when `--json` is used

JSON output is intended for schedulers, wrappers, and operators who want machine-readable
results without parsing logs.

The JSON payload includes:

- application name and version
- environment, dry-run state, host label, and UTC run timestamp
- configured targets and providers
- summary counters
- per-target and per-provider results
- notifications sent
- exit code
- operator-safe error information for failure paths

Secrets are never included in JSON output.

## Exit codes

- `0`: completed successfully, no listings found
- `20`: completed successfully, one or more listings found
- `30`: completed successfully, no listings found, but one or more provider checks failed
- `1`: invalid configuration or unrecoverable application failure

If a listing is found and notification delivery fails, the process exits with `1`.

## Operational outcomes

### Listing found

- the run exits with `20`
- one alert message is sent through the enabled notifiers
- if a notifier fails, the run instead exits with `1`
- provider-specific special return codes that indicate resolver or provider problems are not
  treated as listings

### Provider errors only

- the run exits with `30`
- the target IPs must not be treated as clean
- inspect provider `error_kind` values before deciding whether to re-run
- listing notifications are not sent for provider-error-only runs
- for Spamhaus public mirrors, `127.255.255.252`, `127.255.255.254`, and
  `127.255.255.255` are treated as provider errors, not blacklist listings

### Notification failure

- the run exits with `1`
- inspect logs or JSON for:
  - `failed_channel`
  - `attempted_notification_channels`
  - `notifications_sent_before_failure`
- follow the response steps in [`docs/runbook.md`](runbook.md)

## Provider error kinds

Provider failures are classified explicitly:

- `timeout`
- `open_resolver`
- `no_answer`
- `no_nameservers`
- `dns_exception`
- `unexpected`

`NXDOMAIN` is not an error. It is treated as a clean provider result.

## Secret handling

- keep runtime env files out of version control
- inject notifier credentials through environment variables
- never place Telegram bot tokens or Discord webhook URLs in docs, scripts, or source
  files
- rotate credentials if they are ever exposed

More detailed operational notes live in [`docs/security.md`](security.md).

## Systemd operations

Useful commands:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mail-rbl-monitor.timer
sudo systemctl start mail-rbl-monitor.service
sudo systemctl status mail-rbl-monitor.service
sudo systemctl status mail-rbl-monitor.timer
sudo journalctl -u mail-rbl-monitor.service -n 50
```

See [`deploy/systemd/README.md`](../deploy/systemd/README.md) for the full installation
flow.
