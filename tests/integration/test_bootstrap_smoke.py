from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_BASE_ENV = {
    "APP_ENV": "test",
    "APP_LOG_LEVEL": "INFO",
    "MAIL_RBL_MONITOR_TARGET_IPS": "136.243.71.222",
    "MAIL_RBL_MONITOR_DNSBL_PROVIDERS": "zen.spamhaus.org,b.barracudacentral.org,bl.spamcop.net",
    "MAIL_RBL_MONITOR_ENABLE_TELEGRAM": "false",
    "MAIL_RBL_MONITOR_ENABLE_DISCORD": "false",
    "MAIL_RBL_MONITOR_TIMEOUT_SECONDS": "5",
    "MAIL_RBL_MONITOR_DRY_RUN": "true",
}


def test_bootstrap_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("MAIL_RBL_MONITOR_") and key not in {"APP_ENV", "APP_LOG_LEVEL"}
    }
    env.update(_BASE_ENV)

    result = subprocess.run(
        [sys.executable, "-m", "mail_rbl_monitor", "--dry-run"],
        capture_output=True,
        check=False,
        cwd=repo_root,
        env=env,
        text=True,
    )

    assert result.returncode == 0
    assert "Loaded configuration successfully" in result.stderr
    assert "Providers configured" in result.stderr
    assert "Dry run complete" in result.stderr
