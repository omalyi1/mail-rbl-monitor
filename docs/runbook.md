# Runbook

## First deployment checklist

1. Copy [`.env.prod.example`](../.env.prod.example) to your deployment env file and fill
   the real values.
2. Configure at least one target IPv4 address and one provider.
3. Leave notifier channels disabled until their credentials are ready.
4. Install the `systemd` units from [`deploy/systemd/README.md`](../deploy/systemd/README.md)
   or configure `cron`.

## Validate configuration

Dry-run is the canonical validation path:

```bash
uv run mail-rbl-monitor --dry-run
```

Dry-run JSON validation:

```bash
uv run mail-rbl-monitor --dry-run --json
```

## Real run

Human-readable run:

```bash
uv run mail-rbl-monitor
```

Machine-readable run:

```bash
uv run mail-rbl-monitor --json
```

## Spamhaus DQS verification

1. Keep `zen.spamhaus.org` in `MAIL_RBL_MONITOR_DNSBL_PROVIDERS`.
2. Set `MAIL_RBL_MONITOR_SPAMHAUS_DQS_KEY` in the deployment env file.
3. Run a dry-run first to validate the rest of the configuration:

```bash
uv run mail-rbl-monitor --dry-run
```

4. Perform a real run after the env file is in place:

```bash
uv run mail-rbl-monitor
```

5. If you need to verify the DQS path manually, use placeholder-only commands like:

```bash
dig +short 2.0.0.127.<YOUR_SPAMHAUS_DQS_KEY>.zen.dq.spamhaus.net A
dig +short 2.0.0.127.<YOUR_SPAMHAUS_DQS_KEY>.zen.dq.spamhaus.net TXT
```

Do not paste a real DQS key into docs, tests, issue trackers, or CI logs.
In application JSON output, a Spamhaus result may also show `provider_mode: "dqs"` with
a redacted query name.

## Exit code interpretation

- `0`: completed successfully, no listings found
- `20`: one or more listings found and notifications completed successfully
- `30`: no listings found, but one or more provider checks failed
- `1`: configuration failure, application failure, or notification failure

## JSON interpretation

Success payloads include:

- configured targets and providers
- summary counters
- per-target and per-provider results
- notification channels actually sent

Failure payloads include:

- error `type`
- operator-safe `message`
- `stage` when relevant
- notification channel accounting when a notifier failed

## Response playbook

### Listing found

1. Confirm which target IPs and providers are listed.
2. Review returned `A` and `TXT` data in logs or JSON output.
3. Triage the mail host and its reputation posture.
4. Confirm the intended notification channels delivered successfully.

### Provider errors only

1. Review the `error_kind` values in logs or JSON.
2. Confirm the resolver host has healthy DNS connectivity.
3. If Spamhaus DQS is enabled, verify the key is present and valid in the env file.
4. Re-run manually before assuming the target IP is clean.
5. Treat the run as degraded coverage, not a clean pass.

### Notification failure

1. Inspect logs or JSON for:
   - `failed_channel`
   - `attempted_notification_channels`
   - `notifications_sent_before_failure`
2. Confirm whether an earlier channel already delivered the alert.
3. Repair the failed notifier configuration or remote endpoint.
4. Re-run manually after the notifier path is fixed.
