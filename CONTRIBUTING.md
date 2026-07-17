# Contributing

Thanks for your interest in improving Multimedia Downloader! This repo uses a
single `main` branch; releases are cut as tags (`vX.Y.Z`).

## Project layout

See [Project layout](README.md#project-layout) in the README. In short:
`engine/` (Python: yt-dlp + ffmpeg), `engine_sidecar.py` (stdio IPC),
`web_app.py` (Flask + SSE web backend), `ai/` (OpenRouter orchestration),
`frontend/` (Svelte + TS + Tailwind), `src-tauri/` (Rust shell), `locales/`
(i18n JSON), `tests/`.

## Dev setup

```bash
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
npm install            # Tauri CLI + frontend toolchain (needs Node, Rust, Python 3.8+)
npm run tauri dev      # desktop app in dev mode
# or the web version:
pip install -r requirements-web.txt
npm run build:frontend:web && npm run web
```

## Before you open a PR

- **Tests:** `python -m unittest discover -s tests` (all should pass).
- **Frontend types:** `npm run check` (svelte-check, 0 errors/warnings).
- **i18n:** if you add user-facing strings, add the key to all three
  `locales/*.json` files.
- **Changelog:** note user-facing changes under a new/unreleased section in
  `CHANGELOG.md` (tri-lingual).
- Keep changes focused and match the surrounding code style.

## Commit / PR

Open a PR against `main` with a clear description of what and why. Small,
reviewable PRs are easier to merge. See the PR template for the checklist.

## Reporting bugs / requesting features

Use the [issue templates](https://github.com/SpaceSquare640/Multimedia_Downloader/issues/new/choose).
For security issues, see [SECURITY.md](SECURITY.md).
