# frontend/ — Web UI (Svelte + Vite + TypeScript)

Phase 4 deliverable. The floating window opened by the **AI Assistant** button,
with 4 tabs wired to the engine (via Tauri IPC) and to i18n JSON.

```
src/
├── tabs/
│   ├── VideoTab      video format download   -> engine.Downloader (video)
│   ├── MusicTab      music format download   -> engine.Downloader (audio)
│   ├── ConvertTab    format conversion       -> engine.Converter
│   └── LogTab        run log (unified event stream)
├── ai/               AI assistant panel: render plan, await user confirm (D4)
└── i18n/             load locales/*.json, runtime language switch
```

## Toolchain (installed 2026-07-09)

Dev dependencies are installed project-local in `node_modules/` (see `package.json`):
`@tauri-apps/cli` 2.11.4, `@tauri-apps/api` 2, Svelte 5, Vite, TypeScript, svelte-check.
Verify: `npx tauri --version`.

## Status (Phase 4 — scaffolded 2026-07-09)

Vite + Svelte 5 + TS app is built and verified in the browser (mock transport):
`npm run dev` (port 1420) · `npm run check` (svelte-check, 0 errors) · `npm run build`.

- `src/App.svelte` — floating window, 4 tabs, language switcher, AI button
- `src/tabs/` — DownloadTab (video+audio), ConvertTab, LogTab
- `src/ai/AiPanel.svelte` — D4 advise/confirm shell (Phase 5 wires OpenRouter)
- `src/api.ts` — transport: Tauri IPC when in the desktop shell, mock in a browser
- `src/store.ts` — lang / logs / progress / busy stores
- `src/i18n/` — loads shared `../../../locales/*.json`

The desktop shell (`../src-tauri`, Rust) is scaffolded; run `cargo tauri dev`
from `../src-tauri` to compile and run the real desktop app.

Note: `typescript` is pinned to ^5 — svelte-check is not yet compatible with TS 7.
