# AFWIP — Air Force Wargame: Indo-Pacific

A digital version of the AFWIP classroom board wargame that runs in your web
browser. It includes trained AI opponents (three difficulties), an optional
GPT opponent, hotseat play, and two-device play over a local network — no
account, no internet required (except the one-time setup download, and the GPT
opponent if you use it).

This is the **game only** — trimmed for easy download and local play. (The
research/RL-training code lives in the separate development repository.)

---

## Quick start (no setup)

You need **Python 3.10 or newer** (3.11 recommended) installed. The launcher
creates its own local environment on first run.

- **macOS:** double-click **`run.command`** (first time: right-click → Open → Open).
- **Windows:** double-click **`run.bat`**.
- **Linux / any terminal:** `./run.sh`

The first launch takes ~30 seconds to install and needs internet once; later
launches start in a couple of seconds. Your browser opens automatically at
<http://127.0.0.1:8000>. Leave the window open while you play; close it (or
press Ctrl-C) to stop.

### Run it manually

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m afwip.web                 # opens http://127.0.0.1:8000
```

Options: `python -m afwip.web --port 8080` (different port),
`--no-browser` (don't auto-open).

---

## Play modes

- **Practice vs Agent** — play one side against the computer.
- **Watch Agents** — spectate an AI-vs-AI game.
- **Two Players (one device)** — hotseat, passing the screen between turns.
- **Two Players (network)** — two people, two devices, one game (see below).

### AI opponents

Three trained difficulties — **Easy**, **Medium**, **Best** — run locally from
the bundled `models/*.onnx` files. No GPU or extra setup needed.

### GPT opponent (optional)

Pick **GPT (OpenAI)** as the opponent and paste your own OpenAI API key into the
field that appears. The key is used only by this app on your machine (browser →
your local server → OpenAI) — it is never logged, saved to disk by the server,
or included in any game data. It is remembered in your browser (localStorage) so
you don't have to re-paste it; clear it there any time.

---

## Two-device play on the same network

Two people on the same Wi-Fi / LAN can play one game on two devices, each seeing
only their own side's fog of war.

1. On the **host** machine, start the server so other devices can reach it:

   ```bash
   python -m afwip.web --host 0.0.0.0
   ```

   (or `./run.sh --host 0.0.0.0`)

2. Find the host's LAN IP address:
   - macOS: `ipconfig getifaddr en0`
   - Windows: `ipconfig` (look for IPv4 Address)
   - Linux: `hostname -I`

3. **Host:** open <http://127.0.0.1:8000>, choose **Two Players (network)**,
   pick your side, and **Start Game**. Note the **game code** shown at the top.

4. **Other player:** on their device, open `http://<host-ip>:8000`, enter the
   **game code**, choose the other side, and **Join Game**.

Moves sync automatically within a second or two. Each device can only act for
its own side. (This is classroom-grade: anyone on your network who has the game
code can join — don't expose the port to the open internet.)

---

## Download without Python (standalone app)

A double-click desktop build (no Python needed) can be produced with
PyInstaller — see [`packaging/`](packaging/). It bundles the browser UI and the
AI models into a single `AFWIP.app` (macOS) / `AFWIP.exe` (Windows).

---

## Running the tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

---

## Advisor context pack (`pme_materials/`)

`pme_materials/` is a standalone rules + doctrine reference pack meant to be
loaded into an external AI assistant that coaches a human player. It is not used
by the game itself — it's included for instructors who want to run a live AI
advisor alongside play.
