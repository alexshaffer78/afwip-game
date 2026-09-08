@echo off
rem Build the standalone Windows app (AFWIP.exe) with PyInstaller.
rem
rem   packaging\build_windows.bat
rem
rem RUN THIS ON A WINDOWS MACHINE (you cannot cross-build a Windows exe on a Mac).
rem Requires Python 3.11+ on PATH to BUILD. The resulting app needs NO Python to RUN.
rem Produces:  dist\AFWIP\  (a folder containing AFWIP.exe) -- zip that folder to share.
setlocal
cd /d "%~dp0.."

if not exist .build-venv (
  echo [build] creating build venv...
  python -m venv .build-venv || goto :err
  rem Use `python -m pip` (not the pip.exe wrapper) so pip can upgrade itself on
  rem Windows; harmless if it declines. Upgrading pip is optional -- an older pip
  rem installs the pinned deps fine -- so this step never fails the build.
  .build-venv\Scripts\python -m pip install --quiet --upgrade pip
  .build-venv\Scripts\python -m pip install --quiet -r requirements-app.txt pyinstaller || goto :err
)

echo [build] building AFWIP.exe...
.build-venv\Scripts\pyinstaller packaging\AFWIP.spec --noconfirm --clean || goto :err

echo [build] done -^> dist\AFWIP\AFWIP.exe
echo [build] Right-click dist\AFWIP  -^>  Send to  -^>  Compressed (zipped) folder  to share.
goto :eof

:err
echo [build] build failed - is Python 3.11+ installed and on PATH?
exit /b 1
