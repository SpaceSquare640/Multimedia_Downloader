import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "node:path";

// Tauri expects a fixed dev port; locales live one level up (shared with Python),
// so allow Vite's dev server to read the parent directory.
export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  clearScreen: false,
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
