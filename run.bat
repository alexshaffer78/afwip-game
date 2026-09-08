@echo off
rem One-command classroom launcher (Windows):
rem   run.bat            start the game and open the browser
rem First run creates .venv and installs the runtime (needs internet once);
rem later runs are fast. Needs Python 3.10+ (3.11 recommended).
cd /d "%~dp0"

rem Prefer Python 3.11 via the py launcher; fall back to whatever `python` is.
set "PYCMD=python"
py -3.11 -c "import sys" >nul 2>&1 && set "PYCMD=py -3.11"

rem A sentinel marks a COMPLETE setup. If it's missing (never set up, or a prior
rem setup was interrupted/failed), start clean -- otherwise a half-built .venv
rem silently runs with missing packages and 500s on requests.
if not exist .venv\.afwip-ready (
  echo [afwip] first-time setup ^(needs internet^)...
  if exist .venv rmdir /s /q .venv
  %PYCMD% -m venv .venv || goto :err
  .venv\Scripts\python -m pip install --quiet --upgrade pip
  .venv\Scripts\python -m pip install --quiet -r requirements.txt || goto :installfail
  type nul > .venv\.afwip-ready
)

echo [afwip] starting - your browser opens at http://127.0.0.1:8000 (close this window to stop)
.venv\Scripts\python -m afwip.web %*
goto :eof

:err
echo [afwip] Setup failed. Install Python 3.11 from https://www.python.org/downloads/
echo         (check "Add python.exe to PATH"), then run this again.
exit /b 1

:installfail
echo [afwip] Could not install the packages (network?). Removing the partial setup;
echo         re-run this to try again.
if exist .venv rmdir /s /q .venv
exit /b 1
