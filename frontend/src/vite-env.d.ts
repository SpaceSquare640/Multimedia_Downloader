/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** "web" when built via `build:web` to talk to web_app.py; otherwise undefined. */
  readonly VITE_BACKEND?: "web";
}
