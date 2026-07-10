/**
 * Transport abstraction between the UI and the engine.
 *
 * Under Tauri, calls are forwarded to Rust IPC commands (which talk to the
 * Python engine sidecar); in a plain browser (vite dev / preview) a mock
 * implementation simulates the engine so the UI is fully previewable without
 * the desktop shell. Both emit the SAME event shape the sidecar defines, so
 * the UI code is identical in either environment.
 *
 * ⚠️ SCOPE NOTE (2026-07-10): V4.0's ONLY real production target is the Tauri
 * desktop app. There is currently NO HTTP/WebSocket backend — opening this
 * frontend in a plain browser (outside Tauri) is DEV-PREVIEW ONLY: MockApi
 * fakes progress with setTimeout and never touches yt-dlp/ffmpeg. This is a
 * deliberate scope decision, not an unfinished feature — V3.0's `web_app.py`
 * (a real deployable Flask backend) has no V4.0 equivalent yet. Whether V4.0
 * gets a real standalone web deployment is still undecided; see
 * `System_Architecture/V4.0 System Architecture.md` §8 in the Obsidian vault.
 * Do not build toward "the web version works for real" without re-confirming
 * scope with the user first.
 */

export type Formats = {
  video: string[];
  audio: string[];
  quality: string[];
  browsers: string[];
};

export type EngineEvent =
  | { type: "log"; level: string; key: string; fmt?: Record<string, unknown> }
  | { type: "progress"; pct: number; speed: string; eta: string }
  | { type: "item_start"; index: number; total: number; url: string }
  | { type: "task_update"; label: string; kind: string; status: string; error: string };

export type DownloadArgs = {
  urls: string[];
  mode: "video" | "audio";
  video_fmt: string;
  audio_fmt: string;
  quality: string;
  save_path: string;
  browser?: string;
};

export type ConvertArgs = {
  files: string[];
  dst_fmt: string;
  save_path: string;
};

// ── AI assistant types (Phase 5) ─────────────────────────────────────────────
// Mirrors engine.queue.Task on the Python side — this is what run_queue expects.
export type AiDownloadTask = {
  kind: "download";
  label: string;
  url: string;
  options: {
    save_path: string;
    mode: "video" | "audio";
    video_fmt: string;
    audio_fmt: string;
    quality: string;
    browser: string;
  };
};
export type AiConvertTask = {
  kind: "convert";
  label: string;
  src_path: string;
  dst_path: string;
};
export type AiTask = AiDownloadTask | AiConvertTask;

export type AiPlan = {
  summary: string;
  tasks: AiTask[];
  warnings: string[];
};

export type AiContext = { save_path: string; browser: string };

export type QueueResultTask = { kind: string; label: string; status: string; error: string };

export interface Api {
  getFormats(): Promise<Formats>;
  getLocales(): Promise<Record<string, string>>;
  startDownload(args: DownloadArgs): Promise<void>;
  startConvert(args: ConvertArgs): Promise<void>;
  aiPlan(apiKey: string, prompt: string, context: AiContext): Promise<AiPlan>;
  runQueue(tasks: AiTask[]): Promise<{ tasks: QueueResultTask[] }>;
  stop(): Promise<void>;
  onEvent(cb: (e: EngineEvent) => void): () => void;
}

const isTauri =
  typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

// ── Real (Tauri) transport ────────────────────────────────────────────────
class TauriApi implements Api {
  private async invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
    const { invoke } = await import("@tauri-apps/api/core");
    return invoke<T>(cmd, args);
  }
  getFormats() { return this.invoke<Formats>("get_formats"); }
  getLocales() { return this.invoke<Record<string, string>>("get_locales"); }
  startDownload(args: DownloadArgs) { return this.invoke<void>("start_download", { args }); }
  startConvert(args: ConvertArgs) { return this.invoke<void>("start_convert", { args }); }
  aiPlan(apiKey: string, prompt: string, context: AiContext) {
    return this.invoke<AiPlan>("ai_plan", { args: { api_key: apiKey, prompt, context } });
  }
  runQueue(tasks: AiTask[]) {
    return this.invoke<{ tasks: QueueResultTask[] }>("run_queue", { args: { tasks } });
  }
  stop() { return this.invoke<void>("stop_engine"); }
  onEvent(cb: (e: EngineEvent) => void): () => void {
    let unlisten: (() => void) | undefined;
    import("@tauri-apps/api/event").then(({ listen }) =>
      listen<EngineEvent>("engine-event", (ev) => cb(ev.payload)).then((u) => (unlisten = u)),
    );
    return () => unlisten?.();
  }
}

// ── Mock (browser) transport ────────────────────────────────────────────────
const FORMATS: Formats = {
  video: ["mp4", "mkv", "mov", "avi", "webm", "flv", "wmv", "ts", "m4v", "3gp"],
  audio: ["mp3", "flac", "aac", "wav", "ogg", "m4a", "opus", "wma"],
  quality: ["best", "1080p", "720p", "480p", "360p", "worst"],
  browsers: ["none", "chrome", "firefox", "edge", "safari", "brave", "opera", "chromium"],
};

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

class MockApi implements Api {
  private listeners = new Set<(e: EngineEvent) => void>();
  private stopped = false;

  private emit(e: EngineEvent) { this.listeners.forEach((cb) => cb(e)); }

  getFormats() { return Promise.resolve(FORMATS); }
  getLocales() {
    return Promise.resolve({ en: "English", zh_tw: "繁體中文", zh_cn: "简体中文" });
  }

  async startDownload(args: DownloadArgs) {
    this.stopped = false;
    const urls = args.urls.filter((u) => u.trim());
    const total = urls.length;
    this.emit({ type: "log", level: "info", key: "log_start_batch", fmt: { n: total } });
    for (let i = 0; i < total; i++) {
      if (this.stopped) {
        this.emit({ type: "log", level: "warn", key: "log_stopped_dl" });
        return;
      }
      const idx = i + 1;
      this.emit({ type: "item_start", index: idx, total, url: urls[i] });
      this.emit({ type: "log", level: "info", key: "log_item_downloading", fmt: { i: idx, t: total, url: urls[i] } });
      for (const pct of [20, 55, 90, 100]) {
        if (this.stopped) break;
        await delay(180);
        this.emit({ type: "progress", pct, speed: "3.4MiB/s", eta: pct < 100 ? "00:03" : "--" });
      }
      this.emit({ type: "log", level: "ok", key: "log_item_done", fmt: { i: idx, t: total } });
    }
    this.emit({ type: "log", level: "ok", key: "log_all_done", fmt: { t: total } });
  }

  async startConvert(args: ConvertArgs) {
    this.stopped = false;
    const files = args.files.filter((f) => f.trim());
    const total = files.length;
    for (let i = 0; i < total; i++) {
      if (this.stopped) {
        this.emit({ type: "log", level: "warn", key: "log_convert_stopped" });
        return;
      }
      const idx = i + 1;
      const name = files[i].split(/[\\/]/).pop() ?? files[i];
      const dst = name.replace(/\.[^.]+$/, "") + "." + args.dst_fmt;
      this.emit({ type: "log", level: "info", key: "log_convert_start", fmt: { i: idx, t: total, src: name, dst } });
      await delay(320);
      this.emit({ type: "log", level: "ok", key: "log_convert_done", fmt: { i: idx, t: total, name: dst } });
    }
    this.emit({ type: "log", level: "ok", key: "log_all_converted", fmt: { t: total } });
  }

  stop() { this.stopped = true; return Promise.resolve(); }

  // Naive heuristic "planner" so the AI panel is demoable without a real API
  // key or network access: pull URLs / file paths out of the free-text prompt.
  async aiPlan(_apiKey: string, prompt: string, context: AiContext): Promise<AiPlan> {
    this.emit({ type: "log", level: "info", key: "log_ai_planning_start" });
    await delay(300);
    this.emit({ type: "log", level: "info", key: "log_ai_executing" });
    await delay(300);
    this.emit({ type: "log", level: "info", key: "log_ai_checking" });
    await delay(200);

    const urls = Array.from(prompt.matchAll(/https?:\/\/\S+/g)).map((m) => m[0]);
    const files = Array.from(
      prompt.matchAll(/[^\s"']+\.(mkv|mov|avi|webm|flv|wmv|ts|m4v|3gp|mp4|mp3|wav|flac)/gi),
    ).map((m) => m[0]);

    const savePath = context.save_path || "C:\\Downloads";
    const tasks: AiTask[] = [];
    const warnings: string[] = [];

    for (const url of urls) {
      tasks.push({
        kind: "download", label: url, url,
        options: { save_path: savePath, mode: "video", video_fmt: "mp4",
                  audio_fmt: "mp3", quality: "best", browser: context.browser || "none" },
      });
    }
    for (const f of files) {
      const dstFmt = /\bmp3\b/i.test(prompt) ? "mp3" : "mp4";
      const name = f.split(/[\\/]/).pop() ?? f;
      const dst = name.replace(/\.[^.]+$/, "") + "." + dstFmt;
      tasks.push({ kind: "convert", label: name, src_path: f, dst_path: savePath + "\\" + dst });
    }
    if (tasks.length === 0) {
      warnings.push("mock: no URL or file path found in the prompt — try mentioning one explicitly");
    }

    this.emit({ type: "log", level: "ok", key: "log_ai_plan_ready", fmt: { n: tasks.length } });
    return {
      summary: tasks.length ? `${tasks.length} task(s) inferred from your request (mock)` : "No tasks inferred (mock)",
      tasks,
      warnings,
    };
  }

  async runQueue(tasks: AiTask[]): Promise<{ tasks: QueueResultTask[] }> {
    this.stopped = false;
    const total = tasks.length;
    this.emit({ type: "log", level: "info", key: "log_queue_start", fmt: { n: total } });

    const results: QueueResultTask[] = [];
    let ok = 0;
    for (let i = 0; i < total; i++) {
      const task = tasks[i];
      if (this.stopped) {
        this.emit({ type: "log", level: "warn", key: "log_queue_stopped" });
        for (const rest of tasks.slice(i)) {
          this.emit({ type: "task_update", label: rest.label, kind: rest.kind, status: "skipped", error: "" });
          results.push({ kind: rest.kind, label: rest.label, status: "skipped", error: "" });
        }
        break;
      }
      this.emit({ type: "task_update", label: task.label, kind: task.kind, status: "running", error: "" });
      if (task.kind === "download") {
        this.emit({ type: "item_start", index: i + 1, total, url: task.url });
        for (const pct of [30, 70, 100]) {
          await delay(150);
          this.emit({ type: "progress", pct, speed: "3.4MiB/s", eta: pct < 100 ? "00:02" : "--" });
        }
      } else {
        this.emit({ type: "log", level: "info", key: "log_convert_start",
                   fmt: { i: i + 1, t: total, src: task.label, dst: task.dst_path } });
        await delay(280);
      }
      this.emit({ type: "task_update", label: task.label, kind: task.kind, status: "done", error: "" });
      results.push({ kind: task.kind, label: task.label, status: "done", error: "" });
      ok++;
    }
    this.emit({ type: "log", level: "ok", key: "log_queue_done", fmt: { ok, fail: total - ok, t: total } });
    return { tasks: results };
  }

  onEvent(cb: (e: EngineEvent) => void): () => void {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }
}

export const api: Api = isTauri ? new TauriApi() : new MockApi();
export const IS_MOCK = !isTauri;
/** True when running inside the Tauri desktop shell (native dialogs, IPC…). */
export const IS_TAURI = isTauri;
export { FORMATS as MOCK_FORMATS };
