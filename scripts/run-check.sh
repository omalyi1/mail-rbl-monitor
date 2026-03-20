#!/usr/bin/env bash
set -euo pipefail

uv run python -m mail_rbl_monitor "$@"
