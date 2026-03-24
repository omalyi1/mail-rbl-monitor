# Security

This document covers deployment and operational security guidance. Public vulnerability
reporting expectations live in [`SECURITY.md`](../SECURITY.md).

## Secrets handling

- keep real notifier credentials out of version control
- do not commit `.env`, copied production env files, or pasted secrets
- leave secret fields blank in examples such as [`.env.prod.example`](../.env.prod.example)
- inject Telegram bot tokens and Discord webhook URLs through environment files or a
  secure secret manager
- treat `MAIL_RBL_MONITOR_SPAMHAUS_DQS_KEY` as a secret and store it the same way
- never print a real DQS key in CI logs, issue templates, or pasted troubleshooting output

## Least-privilege deployment

- run the service under a dedicated non-root account
- keep the environment file owned by root or the service account
- prefer restrictive permissions such as `chmod 600 /etc/mail-rbl-monitor/mail-rbl-monitor.env`
- use `systemd` `User=` and `Group=` settings instead of running the service as root

## Operator-facing safety

- secrets must never appear in logs
- secrets must never appear in JSON output
- notification failures are rendered with stable operator-safe messages
- alert messages include operational context, but not credentials or secret URLs
- outbound `httpx` and `httpcore` request-line logs are suppressed at operator-facing log
  levels so request URLs do not leak Telegram bot tokens or Discord webhook paths
- Spamhaus DQS query names are redacted in operator-facing results and JSON output

## What not to commit

- Telegram bot tokens
- Discord webhook URLs
- Spamhaus DQS keys
- copied production env files
- shell history snippets containing secrets

## Basic operational notes

- use dry-run to validate configuration before enabling live notifications
- if notification delivery fails, treat the run as failed even if a listing was found
- never paste a real DQS key into `dig` examples, issue trackers, or CI output
- rotate credentials if they are ever pasted into chat, logs, or issue trackers
