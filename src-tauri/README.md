# src-tauri/ — Tauri shell (Rust)

Desktop shell (Windows / Linux / macOS). Hosts the `frontend/` web UI in a
native window and bridges it to the Python `engine_sidecar.py`.

## Files

- `Cargo.toml` — Tauri 2 dependencies
- `tauri.conf.json` — window, dev URL (`http://localhost:1420`), before-dev/build hooks
- `capabilities/default.json` — window permissions
- `build.rs` — `tauri_build`
- `src/main.rs` — IPC commands + sidecar management

## IPC commands (→ `frontend/src/api.ts` `TauriApi`)

| command | kind | maps to sidecar |
| --- | --- | --- |
| `get_formats` | one-shot | `formats` |
| `get_locales` | one-shot | `locales` (returns the `{code:name}` map) |
| `start_download` | streaming | `download` |
| `start_convert` | streaming | `convert` |
| `run_queue` | streaming | `run_queue` |
| `stop_engine` | — | kills the current sidecar child |

**Model:** one Python sidecar process **per operation**. Streaming ops emit each
sidecar event to the webview as the `engine-event` Tauri event and finish on the
terminal response; `stop_engine` kills the child (cooperative cancel for free).

## ⚠️ Status

Rust source written but **not yet compiled** (authoring env can't run `tauri dev`).
Prerequisites verified 2026-07-09: WebView2, VS Build Tools 2022 (MSVC), Rust
1.96 MSVC toolchain all present; `cargo generate-lockfile` resolves cleanly
(tauri 2.11.5, 417 crates); icons generated. To run, from **`Version4.0/`** (the
parent, NOT this folder — that's where the CLI detects `src-tauri/`):

```bash
npm install            # once, installs the Tauri CLI at the root
npm run tauri dev      # starts vite (beforeDevCommand) + compiles + opens window
```

TODO(Phase 6): bundle a Python runtime instead of spawning PATH `python`;
add secure OpenRouter API-key storage (Phase 5, decision D4).
