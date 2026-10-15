# Frontend

The Svelte 5, TypeScript, and Vite interface is shared by the Tauri desktop app
and the Flask web app. It provides video and audio downloads, format conversion,
an activity log, a built-in manual, and an AI assistant that requires confirmation
before it executes a proposed task queue.

## Transports

`src/api.ts` selects the backend at runtime or build time:

- **Tauri:** invokes Rust commands, which communicate with the Python sidecar.
- **Web:** uses HTTP requests and server-sent events from `web_app.py`; build
  with `npm run build:web` from this directory.
- **Mock:** simulates operations in a plain browser preview and does not download
  or convert files.

The interface and Python engine share the locale files in `../locales/`.

## Commands

Run these from `frontend/`:

```bash
npm run dev       # Vite development server
npm run check     # Svelte and TypeScript checks
npm run build     # Desktop frontend build
npm run build:web # Web frontend build
```

For the desktop app, run `npm run tauri dev` from the repository root. For the
full web app, build the web frontend and start the Flask backend as described in
the root README.
