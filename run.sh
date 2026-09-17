#!/usr/bin/env sh
# Linux/macOS convenience wrapper. The setup logic lives in run.py.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_DIR/run.py" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$SCRIPT_DIR/run.py" "$@"
else
    echo "ERROR: Python 3.11 or newer is required." >&2
    exit 1
fi
