"""
Desktop entry point for the packaged AFWIP app (PyInstaller build).

Starts the local FastAPI server on a free port and opens the default browser,
then runs blocking so the process (and the macOS .app / Windows .exe) stays
alive until the user quits it.

Environment overrides (testing / advanced use):
  AFWIP_PORT        serve on this exact port instead of an auto-picked free one
  AFWIP_NO_BROWSER  set to any value to skip auto-opening the browser
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import webbrowser

# A PyInstaller --windowed app has no console, so sys.stdout / sys.stderr are
# None (always on Windows; on macOS when launched from Finder). uvicorn's log
# formatter calls sys.stdout.isatty(), and print() writes to sys.stdout — both
# crash on None. Give them a real (devnull) stream so the app runs headless.
for _stream in ("stdout", "stderr"):
    if getattr(sys, _stream, None) is None:
        try:
            setattr(sys, _stream, open(os.devnull, "w"))
        except OSError:
            pass


def _free_port(preferred: int = 8000) -> int:
    """Return `preferred` if free, otherwise any OS-assigned free local port."""
    for candidate in (preferred, 0):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", candidate))
            return s.getsockname()[1]
        except OSError:
            continue
        finally:
            s.close()
    return preferred


def main() -> None:
    import uvicorn
    from afwip.web.app import app

    port = int(os.environ.get("AFWIP_PORT") or _free_port(8000))
    url = f"http://127.0.0.1:{port}"
    if not os.environ.get("AFWIP_NO_BROWSER"):
        # Delay so the server is listening by the time the browser requests it.
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"AFWIP is running at {url}")
    print("Keep this app open while you play; quit it to stop the game.")
    # log_config=None skips uvicorn's colorized dictConfig entirely — belt and
    # suspenders for the no-console case (the stdout guard above already handles
    # the isatty() call).
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning",
                log_config=None)


if __name__ == "__main__":
    main()
