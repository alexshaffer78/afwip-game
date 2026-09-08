# AFWIP.spec — PyInstaller build spec for the standalone AFWIP desktop app.
#
# Produces a no-Python-required bundle:
#   macOS   -> dist/AFWIP.app         (double-click in Finder)
#   Windows -> dist/AFWIP/AFWIP.exe   (double-click)
#
# Build (from the repo root, in a venv with the app runtime + pyinstaller):
#   pyinstaller packaging/AFWIP.spec --noconfirm
#
# The built frontend (web/dist, with card/token art) is bundled as data and
# located at runtime via sys._MEIPASS (see afwip/web/app.py).

import os as _os
import sys as _sys

from PyInstaller.utils.hooks import collect_all, copy_metadata

# SPECPATH is the directory containing this spec (packaging/); the repo root is
# its parent. Absolute paths so the build works from any CWD.
_ROOT = _os.path.abspath(_os.path.join(SPECPATH, ".."))
_SCRIPT = _os.path.join(SPECPATH, "afwip_desktop.py")

datas = [
    (_os.path.join(_ROOT, "web", "dist"), "web/dist"),  # UI+art -> _MEIPASS/web/dist
    (_os.path.join(_ROOT, "models"), "models"),          # trained AI opponents -> _MEIPASS/models
]
binaries = []
hiddenimports = []

# uvicorn loads its protocol/loop/lifespan implementations dynamically.
_uv_datas, _uv_bins, _uv_hidden = collect_all("uvicorn")
datas += _uv_datas
binaries += _uv_bins
hiddenimports += _uv_hidden

# Some packages read their version via importlib.metadata at import time.
for _meta in ("gymnasium", "pettingzoo", "pydantic", "fastapi", "starlette", "uvicorn"):
    try:
        datas += copy_metadata(_meta)
    except Exception:
        pass

a = Analysis(
    [_SCRIPT],
    pathex=[_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    # Keep the bundle small: the desktop app never needs the training stack.
    excludes=["torch", "stable_baselines3", "sb3_contrib", "supersuit",
              "tensorboard", "matplotlib", "tkinter", "IPython", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AFWIP",
    console=False,          # no terminal window; the app opens the browser
    disable_windowed_traceback=False,
)

coll = COLLECT(exe, a.binaries, a.datas, name="AFWIP")

if _sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="AFWIP.app",
        icon=None,
        bundle_identifier="mil.af.afwi.afwip",
        info_plist={
            "CFBundleName": "AFWIP",
            "CFBundleDisplayName": "AFWIP",
            "CFBundleShortVersionString": "1.0",
            "NSHighResolutionCapable": True,
            # It's a local server app, not a document editor.
            "LSBackgroundOnly": False,
        },
    )
