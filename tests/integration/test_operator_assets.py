from __future__ import annotations

from pathlib import Path


def test_env_prod_example_exists_and_matches_current_settings_surface() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env_prod_example = repo_root / ".env.prod.example"

    text = env_prod_example.read_text(encoding="utf-8")
    keys = {
        line.split("=", 1)[0]
        for line in text.splitlines()
        if line and not line.startswith("#") and "=" in line
    }

    assert keys == {
        "APP_ENV",
        "APP_LOG_LEVEL",
        "MAIL_RBL_MONITOR_DRY_RUN",
        "MAIL_RBL_MONITOR_TIMEOUT_SECONDS",
        "MAIL_RBL_MONITOR_TARGET_IPS",
        "MAIL_RBL_MONITOR_TARGET_HOSTS",
        "MAIL_RBL_MONITOR_DNSBL_PROVIDERS",
        "MAIL_RBL_MONITOR_ENABLE_TELEGRAM",
        "MAIL_RBL_MONITOR_TELEGRAM_BOT_TOKEN",
        "MAIL_RBL_MONITOR_TELEGRAM_CHAT_ID",
        "MAIL_RBL_MONITOR_ENABLE_DISCORD",
        "MAIL_RBL_MONITOR_DISCORD_WEBHOOK_URL",
        "MAIL_RBL_MONITOR_HOST_LABEL",
        "MAIL_RBL_MONITOR_INCLUDE_HOSTNAME_IN_ALERTS",
        "MAIL_RBL_MONITOR_INCLUDE_CHECKED_AT_IN_ALERTS",
        "MAIL_RBL_MONITOR_ALERT_TIMEZONE",
    }
    assert "MAIL_RBL_MONITOR_TELEGRAM_BOT_TOKEN=\n" in text
    assert "MAIL_RBL_MONITOR_DISCORD_WEBHOOK_URL=\n" in text
    assert "MAIL_RBL_MONITOR_INCLUDE_UTC_TIMESTAMP_IN_ALERTS" not in text
    assert "telegram-token" not in text
    assert "discord.example/webhook" not in text


def test_ci_workflow_exists_and_runs_expected_quality_checks() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workflow = repo_root / ".github" / "workflows" / "ci.yml"

    text = workflow.read_text(encoding="utf-8")

    assert 'python-version: "3.12"' in text
    assert "astral-sh/setup-uv@v5" in text
    assert "uv sync --group dev" in text
    assert "uv run ruff check ." in text
    assert "uv run ruff format --check ." in text
    assert "uv run mypy" in text
    assert "uv run pytest" in text


def test_systemd_readme_exists_and_contains_operator_commands() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    readme = repo_root / "deploy" / "systemd" / "README.md"

    text = readme.read_text(encoding="utf-8")

    assert "systemctl daemon-reload" in text
    assert "systemctl enable --now mail-rbl-monitor.timer" in text
    assert "systemctl start mail-rbl-monitor.service" in text
    assert "journalctl -u mail-rbl-monitor.service" in text


def test_public_release_files_exist() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    assert (repo_root / "LICENSE").is_file()
    assert (repo_root / "CONTRIBUTING.md").is_file()
    assert (repo_root / "CODE_OF_CONDUCT.md").is_file()
    assert (repo_root / "SECURITY.md").is_file()
    assert (repo_root / ".github" / "ISSUE_TEMPLATE" / "bug_report.md").is_file()
    assert (repo_root / ".github" / "ISSUE_TEMPLATE" / "feature_request.md").is_file()
    assert (repo_root / ".github" / "pull_request_template.md").is_file()


def test_public_docs_do_not_contain_absolute_local_paths() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    files = (
        repo_root / "README.md",
        repo_root / "docs" / "local-development.md",
        repo_root / "docs" / "operations.md",
        repo_root / "docs" / "security.md",
        repo_root / "docs" / "runbook.md",
        repo_root / "docs" / "release-checklist.md",
        repo_root / "deploy" / "systemd" / "README.md",
    )

    for path in files:
        assert "/home/om/projects/golos" not in path.read_text(encoding="utf-8")
