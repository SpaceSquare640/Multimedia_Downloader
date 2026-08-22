import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "node:path";
import { readFileSync } from "node:fs";

// The app version lives in the repo-root package.json (kept in sync with
// src-tauri/tauri.conf.json + Cargo.toml at each release, see CHANGELOG) --
// read it here so the UI can compare against the latest GitHub release
// without a separate IPC round-trip for something that never changes at runtime.
const rootPkg = JSON.parse(readFileSync(resolve(__dirname, "../package.json"), "utf-8"));

// Tauri expects a fixed dev port; locales live one level up (shared with Python),
// so allow Vite's dev server to read the parent directory.
export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  clearScreen: false,
  define: {
    __APP_VERSION__: JSON.stringify(rootPkg.version),
  },
  server: {
    port: 1420,
    strictPort: true,
    fs: { allow: [resolve(__dirname, "..")] },
  },
  build: {
    outDir: "dist",
    target: "es2021",
    emptyOutDir: true,
  },
});
