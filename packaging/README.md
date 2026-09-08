# Packaging AFWIP as a standalone desktop app

This builds a **no-Python-required** bundle of the classroom web app with
[PyInstaller]: the recipient double-clicks and plays — nothing to install.

- **macOS** → `AFWIP.app`
- **Windows** → `dist\AFWIP\AFWIP.exe`

Launching it starts a local server and opens the game in the default browser
(`http://127.0.0.1:<free port>`). Everything runs locally; no account or
internet is needed to run it (only to *build* it the first time).

## Build

You need **Python 3.11+** on the build machine. You cannot cross-build: build a
macOS app on a Mac and a Windows exe on Windows.

```bash
# macOS
packaging/build_macos.sh
# -> dist/AFWIP.app  and  dist/AFWIP-macOS-<arch>.zip
```

```bat
:: Windows (run on Windows)
packaging\build_windows.bat
:: -> dist\AFWIP\AFWIP.exe   (zip the dist\AFWIP folder to share)
```

Both scripts create an isolated `.build-venv`, install the minimal runtime
(`requirements-app.txt`) plus PyInstaller, and run `packaging/AFWIP.spec`.

The spec bundles the pre-built frontend (`web/dist`, including all card/token
art) as data; `afwip/web/app.py` finds it at runtime via `sys._MEIPASS`. If you
change the frontend, rebuild it first (`cd web && npm run build`), then rebuild
the app.

## Share it

- **macOS:** share `dist/AFWIP-macOS-<arch>.zip` (zipped with `ditto`, which
  preserves the `.app`). The recipient unzips and double-clicks `AFWIP.app`.
- **Windows:** zip the whole `dist\AFWIP` folder and share it. The recipient
  unzips and double-clicks `AFWIP.exe` (keep the exe next to its files).

## Notes the recipient needs

- **macOS Gatekeeper (unsigned app).** The app is ad-hoc signed but not signed
  with an Apple Developer ID or notarized. When it's **downloaded from the
  internet** (browser, Google Drive, email) macOS quarantines it and blocks the
  first launch — on **Apple Silicon this shows "AFWIP is damaged and can't be
  opened"** (right-click → Open does NOT bypass this one). Fix: remove the
  quarantine flag once, then double-click:
  ```
  xattr -dr com.apple.quarantine /path/to/AFWIP.app
  ```
  (Tip: type `xattr -dr com.apple.quarantine ` — with a trailing space — then
  drag `AFWIP.app` from Finder into Terminal to fill in the path, and press
  Enter.) Apps copied via **USB stick or a local file share are not quarantined**
  and skip this entirely. To remove the warning permanently for every recipient,
  sign + notarize with an Apple Developer ID (see below).
- **Windows SmartScreen.** *"Windows protected your PC"* → **More info → Run
  anyway** (unsigned app).
- **Quit to stop the game.** macOS: press **Cmd-Q**, or right-click the AFWIP
  Dock icon → **Quit**. Windows: close the app. Closing only the browser tab
  does not stop the server.
- **Architecture (macOS).** The `.app` is built for the build machine's CPU —
  `arm64` on Apple Silicon, `x86_64` on Intel. To ship to the other kind of Mac,
  build on that kind (or produce a `universal2` build — not set up here).

## Signing (optional, removes the warnings)

To avoid the Gatekeeper/SmartScreen prompts entirely you'd sign + notarize
(macOS: an Apple Developer ID + `codesign`/`notarytool`; Windows: an
Authenticode code-signing certificate). Not required for classroom use — the
right-click-Open / Run-anyway steps above are enough.

[PyInstaller]: https://pyinstaller.org/
