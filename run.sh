#!/usr/bin/env bash
# One-command classroom launcher (macOS / Linux):
#   ./run.sh              start the game and open the browser
#   ./run.sh --port N     serve on a different port
#   PYTHON=/path ./run.sh use a specific Python (e.g. a conda env)
#
# First run creates a local .venv and installs the minimal runtime (needs
# internet once); later runs start in seconds. Needs Python 3.10+ (3.11
# recommended).
set -euo pipefail
cd "$(dirname "$0")"

# Pick a Python >= 3.10. Honor $PYTHON, else try common names newest-first.
pick_python() {
  if [ -n "${PYTHON:-}" ]; then echo "$PYTHON"; return 0; fi
  for c in python3.11 python3.12 python3.10 python3 python; do
    if command -v "$c" >/dev/null 2>&1 \
       && "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3,10) else 1)' >/dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}

if ! PY=$(pick_python); then
  echo "[afwip] No suitable Python found (need 3.10+, 3.11 recommended)."
  echo "        Install it from https://www.python.org/downloads/ and try again,"
  echo "        or point this at one:  PYTHON=/path/to/python ./run.sh"
  exit 1
fi

# A sentinel marks a COMPLETE setup. If it's missing (never set up, or a prior
# setup was interrupted/failed), start clean and install again — otherwise a
# half-built .venv silently runs with missing packages and 500s on requests.
if [ ! -f .venv/.afwip-ready ]; then
  echo "[afwip] first-time setup (~30s, needs internet) using $("$PY" --version 2>&1)..."
  rm -rf .venv
  "$PY" -m venv .venv
  ./.venv/bin/python -m pip install --quiet --upgrade pip
  if ! ./.venv/bin/python -m pip install --quiet -r requirements.txt; then
    echo "[afwip] setup could not install the packages (network?). Please re-run."
    rm -rf .venv
    exit 1
  fi
  touch .venv/.afwip-ready
fi

echo "[afwip] starting — your browser will open at http://127.0.0.1:8000"
echo "[afwip] leave this window open while you play; press Ctrl-C (or close it) to stop."
exec ./.venv/bin/python -m afwip.web "$@"
