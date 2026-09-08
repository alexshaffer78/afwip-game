#!/usr/bin/env bash
# Double-clickable macOS launcher. Runs run.sh in this Terminal window.
#
# First time you double-click, macOS may say it's from an unidentified
# developer: right-click this file -> Open -> Open (only needed once).
# If double-clicking opens a text editor instead, the file lost its
# "executable" flag in transit -- just open Terminal and run:  bash run.sh
cd "$(dirname "$0")"
bash ./run.sh
echo
echo "AFWIP has stopped. You can close this window."
