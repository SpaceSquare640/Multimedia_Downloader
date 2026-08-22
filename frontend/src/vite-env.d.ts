/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** "web" when built via `build:web` to talk to web_app.py; otherwise undefined. */
  readonly VITE_BACKEND?: "web";
}

/** Injected at build time from the repo-root package.json (see vite.config.ts). */
declare const __APP_VERSION__: string;
