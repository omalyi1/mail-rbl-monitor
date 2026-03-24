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

Secrets are never included in JSON output. If Spamhaus DQS is enabled, serialized query
names stay redacted rather than exposing the real key.

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
- Spamhaus DQS mode does not reuse those public-mirror special-code rules automatically

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
- treat `MAIL_RBL_MONITOR_SPAMHAUS_DQS_KEY` as a secret
- never place Telegram bot tokens or Discord webhook URLs in docs, scripts, or source
  files
- rotate credentials if they are ever exposed

## Spamhaus DQS

Keep `zen.spamhaus.org` in `MAIL_RBL_MONITOR_DNSBL_PROVIDERS`. To enable DQS, set:

```bash
MAIL_RBL_MONITOR_SPAMHAUS_DQS_KEY=<YOUR_SPAMHAUS_DQS_KEY>
```

Leave the key blank to use the existing public-mirror behavior.
If the key is missing, invalid, or unusable, Spamhaus may surface as a provider error
rather than a listing.

Manual operator verification with placeholders only:

```bash
dig +short 2.0.0.127.<YOUR_SPAMHAUS_DQS_KEY>.zen.dq.spamhaus.net A
dig +short 2.0.0.127.<YOUR_SPAMHAUS_DQS_KEY>.zen.dq.spamhaus.net TXT
```

If DQS is active in the application, operator-facing results still use redacted query
names such as `2.0.0.127.<spamhaus-dqs>.zen.dq.spamhaus.net`. JSON output may also show
`provider_mode: "dqs"` for the Spamhaus provider result.

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
