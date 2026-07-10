/** Shared Svelte stores: active language (with reactive translator) and log lines. */

import { writable, derived } from "svelte/store";
import { Translator, DEFAULT_LANG, type Lang } from "./i18n";

export const lang = writable<Lang>(DEFAULT_LANG);

// Keep <html lang> in sync for screen readers / correct font selection.
lang.subscribe((l) => {
  if (typeof document !== "undefined") {
    document.documentElement.lang = l === "zh_tw" ? "zh-Hant" : l === "zh_cn" ? "zh-Hans" : "en";
  }
});

/** Reactive translator function; recomputed whenever `lang` changes. */
export const t = derived(lang, ($lang) => {
  const tr = new Translator($lang);
  return (key: string, params?: Record<string, unknown>) => tr.t(key, params);
});

export type LogEntry = { level: string; text: string; seq: number; ts: string };

const MAX_LOGS = 2000; // cap so an hours-long batch can't grow memory unbounded

let _seq = 0;
export const logs = writable<LogEntry[]>([]);

export function pushLog(level: string, text: string): void {
  const ts = new Date().toLocaleTimeString(undefined, { hour12: false });
  logs.update((l) => {
    const next = [...l, { level, text, seq: _seq++, ts }];
    return next.length > MAX_LOGS ? next.slice(next.length - MAX_LOGS) : next;
  });
}

export function clearLogs(): void {
  logs.set([]);
}

export type Progress = { pct: number; speed: string; eta: string };
export const progress = writable<Progress | null>(null);

/** True while an engine operation (download/convert) is running. */
export const busy = writable(false);
