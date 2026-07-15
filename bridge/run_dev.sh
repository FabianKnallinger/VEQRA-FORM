#!/usr/bin/env bash
# Startet die VEQRA Bridge fuer die Entwicklung (Linux/macOS/Codespace).
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv-bridge" ]; then
    python3 -m venv .venv-bridge
    ./.venv-bridge/bin/pip install --upgrade pip
    ./.venv-bridge/bin/pip install -r requirements.txt
fi

echo "VEQRA Bridge startet auf http://127.0.0.1:8899 (Beenden mit Strg+C)"
exec ./.venv-bridge/bin/python run_bridge.py
