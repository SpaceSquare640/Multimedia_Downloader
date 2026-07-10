/**
 * Theme store: light / dark / system. Default dark (product decision).
 * Persists to localStorage ("mmdl_theme" — must match the inline pre-init
 * script in index.html) and toggles the `dark` class on <html>.
 */

import { writable } from "svelte/store";

export type Theme = "light" | "dark" | "system";
const KEY = "mmdl_theme";

function load(): Theme {
  const v = localStorage.getItem(KEY);
  return v === "light" || v === "dark" || v === "system" ? v : "dark";
}

export const theme = writable<Theme>(load());

const media = matchMedia("(prefers-color-scheme: dark)");

function apply(t: Theme): void {
  const dark = t === "dark" || (t === "system" && media.matches);
  document.documentElement.classList.toggle("dark", dark);
}

theme.subscribe((t) => {
  localStorage.setItem(KEY, t);
  apply(t);
});
// Re-apply when the OS scheme changes while in "system" mode.
media.addEventListener("change", () => {
  const t = load();
  if (t === "system") apply(t);
});

/** Cycle light → dark → system → light (used by the header toggle). */
export function cycleTheme(): void {
  theme.update((t) => (t === "light" ? "dark" : t === "dark" ? "system" : "light"));
}
