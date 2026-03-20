from pathlib import Path


def test_systemd_templates_exist_and_contain_expected_placeholders() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    service_template = repo_root / "deploy" / "systemd" / "mail-rbl-monitor.service"
    timer_template = repo_root / "deploy" / "systemd" / "mail-rbl-monitor.timer"
    readme = repo_root / "deploy" / "systemd" / "README.md"

    service_text = service_template.read_text(encoding="utf-8")
    timer_text = timer_template.read_text(encoding="utf-8")
    readme_text = readme.read_text(encoding="utf-8")

    assert "Type=oneshot" in service_text
    assert "WorkingDirectory=<MAIL_RBL_MONITOR_WORKDIR>" in service_text
    assert "EnvironmentFile=<MAIL_RBL_MONITOR_ENV_FILE>" in service_text
    assert "ExecStart=/usr/bin/env uv run mail-rbl-monitor" in service_text
    assert "UMask=0077" in service_text
    assert "OnCalendar=daily" in timer_text
    assert "Unit=mail-rbl-monitor.service" in timer_text
    assert "mail-rbl-monitor.service" in readme_text
