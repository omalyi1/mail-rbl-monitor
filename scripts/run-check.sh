#!/usr/bin/env bash
set -euo pipefail

uv run mail-rbl-monitor "$@"
