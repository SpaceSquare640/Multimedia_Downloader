# Multimedia Downloader — V4.3.3

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/SpaceSquare640/Multimedia_Downloader?sort=semver)](https://github.com/SpaceSquare640/Multimedia_Downloader/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/SpaceSquare640/Multimedia_Downloader/total)](https://github.com/SpaceSquare640/Multimedia_Downloader/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Web-blue)](#run-as-a-web-app-v41)
[![Built with](https://img.shields.io/badge/built%20with-Tauri%20·%20Svelte%20·%20Python-6E56CF)](#project-layout)

A cross-platform multimedia downloader & format converter built on top of
[yt-dlp](https://github.com/yt-dlp/yt-dlp) and `ffmpeg`, with an AI assistant
for batch automation. Ships as a native desktop app (Windows / Linux / macOS)
built with [Tauri](https://tauri.app), and as a deployable web app.

> This document is in English. For 繁體中文 / 简体中文 documentation, see the
> [Wiki](https://github.com/SpaceSquare640/Multimedia_Downloader/wiki) — the
> app's own UI stays available in all three languages regardless.

---

## Highlights

- **AI Assistant** — describe what you want in plain language ("convert every
  .mkv in this folder to mp4"); the assistant drafts a batch plan and **only
  runs it after you confirm** — nothing executes without your approval.
- **500+ sites** — YouTube, Facebook, Instagram, TikTok, BiliBili, Twitter,
  SoundCloud, Twitch, Vimeo, and every other site yt-dlp supports.
- **Audio extraction** — convert to MP3, FLAC, AAC, WAV, OGG, M4A, Opus, WMA.
- **Format conversion** — transcode any input to any output via ffmpeg
  (bundled — no separate ffmpeg install needed).
- **Tri-language UI** — English (default), Traditional Chinese, Simplified
  Chinese; switchable at runtime.
- **Cookie support** — read from an installed browser, or supply a
  `cookies.txt` for Douyin / Instagram / login-gated platforms.
- **Batch queue** — download or convert many items in one go, with live
  per-item progress and a run log.
- **Built-in User Manual** — a quick reference panel right in the app (header
  book icon), available in all three languages.

> [!NOTE]
> Primarily a desktop app; **V4.1** adds a real, network-deployable web version
> (see [Run as a web app](#run-as-a-web-app-v41) below). Native mobile apps are
> planned for **V5.0**.

## Install (end users)

1. Download the installer for your platform from the [Releases page](https://github.com/SpaceSquare640/Multimedia_Downloader/releases/latest) (Windows: `.exe`
   or `.msi`).
2. Run it and follow the prompts.
3. Launch **Multimedia Downloader** from the Start Menu / Applications.

No separate Python or ffmpeg install is required — both are bundled inside
the app.

## Using the AI Assistant

> [!NOTE]
> The AI Assistant runtime error in the 4.0.0 build is **fixed in v4.1** (the
> planner/summarizer OpenRouter models had been delisted upstream and were
> swapped for current free models).

1. Click the **✨ AI Assistant** button (or press `Ctrl/Cmd+K`).
2. First time only: open **Settings** and paste your own
   [OpenRouter](https://openrouter.ai/keys) API key (stored locally on your
   device only — never bundled, never sent anywhere but OpenRouter).
3. Describe your task, e.g. *"Download
   https://youtube.com/watch?v=... as mp4"* or *"Convert D:\videos\a.mov and
   b.avi to mp4"*.
4. Review the generated plan — **nothing runs yet**.
5. Click **Confirm** to execute, or **Cancel** / **Regenerate**.

## Requirements

| Component | Notes |
| --- | --- |
| Windows 10/11, Linux, or macOS | Desktop app; all three platforms built and published automatically by CI. |
| WebView2 | Pre-installed on modern Windows; the installer will prompt if missing. |
| OpenRouter API key | **Optional** — only needed to use the AI Assistant. Get one free at [openrouter.ai](https://openrouter.ai/keys). |

## Building from source (developers)

```bash
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
npm install                 # installs the Tauri CLI at the project root
npm run tauri dev           # compile + run in dev mode (needs Python 3.8+, Rust, Node)
npm run tauri build         # build an installer locally, if you want one without waiting for CI
```

Official installers for every push tag are built and published automatically
by GitHub Actions (see `.github/workflows/release.yml`) — you don't need to
build locally to cut a release, just push a `vX.Y.Z` tag.

Run the Python test suite: `python -m unittest discover -s tests` (63 tests).

## Run as a web app (V4.1)

The same UI can run as a standalone, deployable web app — no desktop shell —
with a real Flask + SSE backend that drives the *same* engine (real yt-dlp /
ffmpeg, not the browser mock):

```bash
cd Multimedia_Downloader
pip install -r requirements-web.txt   # yt-dlp + Flask (ffmpeg on PATH)
npm run build:frontend:web            # build the frontend in web mode
npm run web                           # serve on http://127.0.0.1:5000
# LAN / server:
HOST=0.0.0.0 PORT=8000 python web_app.py
```

Because it's a browser app, downloaded/converted files land in a **server-side**
folder (`MMDL_DOWNLOADS`, default `./downloads`) retrievable at `/files/<name>`
— leave the Save-Location field blank to use it. It's a single-user model (one
operation at a time, like V3.0's `web_app.py`); for production put it behind a
streaming-friendly WSGI worker, e.g. `gunicorn -k gthread -w 1 --threads 8
web_app:app`, and add your own auth if exposing it beyond localhost.

## Run on Android (Termux)

The desktop app can't run on Android, but the Python engine can — via
[Termux](https://termux.dev). Use it from the terminal (CLI) or as the web UI
in your phone's browser:

```bash
pkg install -y git && git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
bash termux/run-cli.sh download "https://youtu.be/XXXX" -o ~/storage/downloads -f mp4   # CLI
bash termux/run-web.sh                                                                  # web UI
```

Full walkthrough: [termux/README.md](termux/README.md). The CLI ([`cli.py`](cli.py))
also runs on any desktop/server with Python + ffmpeg.

## Run in your terminal (TUI)

Prefer a keyboard-driven interface over the desktop GUI — or you're on a
headless server / SSH session? The desktop, Termux, and web installs all
already had a terminal-friendly path via [`cli.py`](cli.py); **V4.3** adds a
full interactive terminal UI (built with [Textual](https://textual.textualize.io))
with the same Download / Convert / Log tabs as the desktop app, driving the
*same* engine:

```bash
pip install -r requirements-tui.txt   # yt-dlp + textual (ffmpeg on PATH)
python -m tui                         # or: python -m tui --lang zh_tw
```

Keyboard shortcuts: `d` toggles light/dark, `q` quits. The language is fixed
at launch via `--lang` (like `cli.py`) rather than switchable mid-session.

## Project layout

```
Source_Code/
├── src-tauri/    Tauri shell (Rust): window, sidecar management
├── frontend/     Web UI (Svelte + Vite + TS + Tailwind)
├── engine/       Python engine: Downloader / Converter (yt-dlp + ffmpeg)
├── engine_sidecar.py   stdio IPC entrypoint spawned by the Rust shell
├── web_app.py    Flask + SSE backend for the standalone web app (V4.1)
├── cli.py        terminal CLI over the engine (great for Termux / headless)
├── tui/          interactive terminal UI (Textual) over the same engine
├── termux/       Android (Termux) launchers + guide
├── ai/           OpenRouter client + multi-model planning pipeline
├── locales/      en.json / zh_tw.json / zh_cn.json
├── packaging/    PyInstaller spec (used by CI to build the sidecar)
└── tests/        Unit tests
```

## Cookie tips

Some platforms (Douyin, private TikTok, private Instagram) refuse to serve
media without an authenticated cookie:

1. **Browser-direct (easiest)** — select the browser you are logged into in
   the download tab. yt-dlp reads its cookies for you.
2. **Manual file** — export `cookies.txt` with a browser extension (e.g.
   *Get cookies.txt LOCALLY* for Chrome/Edge/Brave, *cookies.txt* for
   Firefox).

## Disclaimer

This software is for personal, lawful use only. Respect each platform's terms
of service and the copyright of content owners.
