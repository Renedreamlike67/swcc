#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(command -v python3 || command -v python)"

if [[ -z "$PYTHON_BIN" ]]; then
  echo "python3 or python is required" >&2
  exit 1
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/scripts/sync-from-claude.py" "$@"
