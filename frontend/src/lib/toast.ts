/** Minimal toast store — no extra dependency, matches the app theme. */

import { writable } from "svelte/store";

export type Toast = { id: number; text: string; kind: "ok" | "err" | "info" };

let seq = 0;
export const toasts = writable<Toast[]>([]);

export function toast(text: string, kind: Toast["kind"] = "info", ms = 3500): void {
  const id = seq++;
  toasts.update((l) => [...l, { id, text, kind }]);
  setTimeout(() => toasts.update((l) => l.filter((t) => t.id !== id)), ms);
}
