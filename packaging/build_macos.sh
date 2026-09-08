#!/usr/bin/env bash
# Build the standalone macOS app bundle (AFWIP.app) with PyInstaller.
#
#   packaging/build_macos.sh
#
# Requires Python 3.11+ to BUILD. The resulting app needs NO Python to RUN.
# Produces:  dist/AFWIP.app  and  dist/AFWIP-macOS-<arch>.zip
#
# The .app is built for the CPU of the build machine (arm64 on Apple Silicon,
# x86_64 on Intel). Build on the architecture you need to ship.
set -euo pipefail
cd "$(dirname "$0")/.."          # repo root

PY=${PYTHON:-python3}
VENV=.build-venv
if [ ! -d "$VENV" ]; then
  echo "[build] creating build venv ($("$PY" --version))..."
  "$PY" -m venv "$VENV"
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet -r requirements-app.txt pyinstaller
fi

echo "[build] building AFWIP.app..."
"$VENV/bin/pyinstaller" packaging/AFWIP.spec --noconfirm --clean

echo "[build] zipping bundle for distribution (ditto preserves the .app)..."
ARCH=$(uname -m)
rm -f "dist/AFWIP-macOS-$ARCH.zip"
ditto -c -k --keepParent "dist/AFWIP.app" "dist/AFWIP-macOS-$ARCH.zip"

echo "[build] done:"
echo "        dist/AFWIP.app"
echo "        dist/AFWIP-macOS-$ARCH.zip   (share this)"
