"""
One-command launcher:  python -m afwip.web  [--port 8000] [--no-browser]

Starts the local FastAPI server and opens the browser at it. Add --host
0.0.0.0 to let another device on the same network connect.
"""

from __future__ import annotations

import argparse
import threading
import webbrowser


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AFWIP local web game")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true",
                        help="don't auto-open the browser")
    args = parser.parse_args(argv)

    import uvicorn
    from afwip.web.app import app

    if not args.no_browser:
        url = f"http://{'127.0.0.1' if args.host == '0.0.0.0' else args.host}:{args.port}"
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
