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

1. On the **host** machine, start the server in network mode:

   ```bash
   python -m afwip.web --lan
   ```

   (or `./run.sh --lan`). This prints the exact URL to share, e.g.:

   ```
   ────────────────────────────────────────────
    AFWIP is hosting a game on your network.
      On THIS computer:            http://127.0.0.1:8000
      Share with the other player: http://192.168.1.42:8000
   ────────────────────────────────────────────
   ```

   (`--lan` is shorthand for `--host 0.0.0.0`. If the URL can't be detected,
   look up the host's IP with `ipconfig getifaddr en0` on macOS, `ipconfig` on
   Windows, or `hostname -I` on Linux.)

2. **Host:** open the *On THIS computer* URL, choose **Two Players (network)**,
   pick your side, and **Start Game**. Note the **game code** shown at the top.

3. **Other player:** on their device, open the *Share with the other player*
   URL, enter the **game code**, choose the other side, and **Join Game**.

Moves sync automatically within a second or two. Each device can only act for
its own side.

**If they can't connect** despite the same Wi-Fi: guest networks and many
university/office networks block device-to-device traffic, and a firewall or VPN
on the host can too. The simplest fix is to have the host turn on a **phone
hotspot** and put both devices on it. (This is classroom-grade — anyone on your
network who has the game code can join, so don't expose the port to the open
internet.)

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
