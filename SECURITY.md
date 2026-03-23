# Security Policy

## Reporting a vulnerability

If you believe you have found a security vulnerability in `mail-rbl-monitor`, do
not open a public GitHub issue for details that could put users at risk.

Preferred reporting path:

- use GitHub's private vulnerability reporting for this repository if it is enabled

If private reporting is not available, contact the repository maintainers through a
private channel before sharing exploit details publicly.

For non-sensitive hardening ideas or documentation improvements, a normal GitHub issue
is fine.

## What to include

Please include:

- affected version, commit, or branch
- a concise description of the issue
- impact and realistic attack scenario
- reproduction steps or proof of concept when safe to share
- any relevant configuration context without secrets

## Scope

This policy covers the maintained source repository and its documented deployment
artifacts, including:

- the Python application under `src/`
- JSON and CLI output behavior
- notification adapters
- env examples and operator assets
- systemd templates and deployment docs

## Response expectations

Maintainers aim to acknowledge reports within 7 days and will provide follow-up as
triage progresses. Resolution timelines depend on severity and maintainer availability.

## Operational security notes

Deployment-focused guidance lives in [docs/security.md](docs/security.md).
