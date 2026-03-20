# Release Checklist

## Pre-release checks

1. Run `uv run ruff check .`
2. Run `uv run ruff format --check .`
3. Run `uv run mypy`
4. Run `uv run pytest`
5. Review [.env.prod.example](/home/om/projects/golos/.env.prod.example)
6. Review the `systemd` templates in [deploy/systemd](/home/om/projects/golos/deploy/systemd)
7. Review docs for command and settings drift

## Deploy checks

1. Confirm the target host has Python 3.12+ and `uv`
2. Confirm the repository is deployed at the intended working directory
3. Confirm the production env file contains the correct targets, providers, and notifier settings
4. Confirm the service account and file permissions are correct
5. Reload `systemd` if unit files changed

## Post-deploy verification

1. Run `uv run mail-rbl-monitor --dry-run`
2. Run `uv run mail-rbl-monitor --dry-run --json`
3. Confirm logs are present and secret-safe
4. If using `systemd`, run the service once manually and inspect `journalctl`
5. Confirm the timer is enabled and scheduled as expected
