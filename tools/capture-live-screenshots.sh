#!/usr/bin/env bash
# Capture screenshots from the running SOC lab using real service UIs where available.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -r tools/requirements-screenshots.txt
python3 -m playwright install chromium
python3 tools/capture-live-screenshots.py "$@"
