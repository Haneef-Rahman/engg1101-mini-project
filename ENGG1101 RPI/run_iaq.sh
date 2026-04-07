#!/usr/bin/env bash
# run_iaq.sh  –  minimal, robust launcher
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# 1. Ensure the venv and required packages exist
python3 "$HERE/bootup.py"

# 2. Run main.py **with the venv’s python** (no shell activation needed)
VENV_PY="$HERE/iaq-env/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo "❌  $VENV_PY not found or not executable.  bootup.py must have failed."
  exit 1
fi

exec "$VENV_PY" "$HERE/main.py" "$@"