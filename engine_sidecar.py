"""
Engine sidecar — the IPC boundary between the Tauri shell and the Python engine.

Protocol (newline-delimited JSON over stdio)
--------------------------------------------
The Tauri shell (Rust) spawns this process and speaks line-oriented JSON:

Requests  (shell -> sidecar), one JSON object per line::

    {"id": "<any>", "cmd": "<name>", "args": {...}}

Responses (sidecar -> shell), the terminal reply to a request::

    {"id": "<same id>", "ok": true,  "result": {...}}
    {"id": "<same id>", "ok": false, "error": "message"}

Events    (sidecar -> shell), streamed while a command runs (no id required)::

    {"type": "log",         "level": "info|ok|warn|err", "key": "<i18n key>", "fmt": {...}}
    {"type": "progress",    "pct": 42.0, "speed": "1.2MiB/s", "eta": "00:12"}
    {"type": "item_start",  "index": 1, "total": 3, "url": "..."}
    {"type": "task_update", "label": "...", "kind": "download|convert",
                            "status": "pending|running|done|error|skipped", "error": ""}

Commands
--------
ping                     -> {"pong": true}
formats                  -> {"video": [...], "audio": [...], "quality": [...], "browsers": [...]}
locales                  -> {"available": {code: name}}
strings   {lang}         -> {"lang": lang, "strings": {key: value}}
download  {urls, options}-> {"results": [[url, ok, error], ...]}     (streams log/progress/item_start)
convert   {files, dst_fmt, save_path, ffmpeg_bin?}
                         -> {"jobs": [{src, dst, status, error}, ...]}  (streams log)
run_queue {tasks}        -> {"tasks": [{kind, label, status, error}, ...]} (streams log/task_update)
ai_plan   {api_key, prompt, context?}
                         -> {"summary": str, "tasks": [...], "warnings": [...]}  (streams log; NEVER
                            executes anything — the shell must call run_queue after user confirms, D4)
ai_summarize {api_key, results}
                         -> {"text": str}
stop                     -> {"stopping": true}   (cooperatively aborts the active op)

The engine emits i18n KEYS, not translated text; the frontend translates them.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from typing import Callable, Optional

import i18n
from ai import Orchestrator, OrchestratorError
from engine import (
    AUDIO_FORMATS,
    BROWSERS,
    QUALITY_PRESETS,
    VIDEO_FORMATS,
    Converter,
    Downloader,
    DownloadOptions,
    Task,
    TaskQueue,
)

Emit = Callable[[dict], None]


def resolve_ffmpeg() -> str:
    """
    Default ffmpeg binary to use.

    In a packaged (frozen) build, the Tauri bundle drops `ffmpeg.exe` next to
    this sidecar executable, so prefer that — the end user needn't have ffmpeg
    on PATH. In source runs, fall back to PATH `ffmpeg`. A caller can always
    override via the command's `ffmpeg_bin` arg.
    """
    if getattr(sys, "frozen", False):
        exe = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        bundled = os.path.join(os.path.dirname(sys.executable), exe)
        if os.path.isfile(bundled):
            return bundled
    return "ffmpeg"


DEFAULT_FFMPEG = resolve_ffmpeg()


class Sidecar:
    """Dispatches IPC requests to the engine, streaming events via ``emit``."""

    def __init__(self, emit: Emit) -> None:
        self._emit = emit
        # The currently running stoppable op (Downloader / Converter / TaskQueue).
        self._active: Optional[object] = None

    # ── Dispatch ──────────────────────────────────────────────────────────────
    def dispatch(self, req: dict) -> dict:
        """Handle one request, return its terminal response dict."""
        rid = req.get("id")
        cmd = req.get("cmd")
        args = req.get("args") or {}
        try:
            handler = getattr(self, f"_cmd_{cmd}", None)
            if handler is None:
                return {"id": rid, "ok": False, "error": f"unknown cmd: {cmd!r}"}
            result = handler(args)
            return {"id": rid, "ok": True, "result": result}
        except Exception as e:  # never let one bad request kill the loop
            return {"id": rid, "ok": False, "error": str(e)}

    # ── Callback factories → JSON events ────────────────────────────────────────
    def _log_cb(self, level: str, key: str, **fmt) -> None:
        self._emit({"type": "log", "level": level, "key": key, "fmt": fmt})

    def _progress_cb(self, pct: float, speed: str, eta: str) -> None:
        self._emit({"type": "progress", "pct": pct, "speed": speed, "eta": eta})

    def _item_start_cb(self, index: int, total: int, url: str) -> None:
        self._emit({"type": "item_start", "index": index, "total": total, "url": url})

    def _task_update_cb(self, task: Task) -> None:
        self._emit({"type": "task_update", "label": task.label, "kind": task.kind,
                    "status": task.status, "error": task.error})

    # ── Commands ────────────────────────────────────────────────────────────────
    def _cmd_ping(self, args: dict) -> dict:
        return {"pong": True}

    def _cmd_formats(self, args: dict) -> dict:
        return {
            "video": VIDEO_FORMATS,
            "audio": AUDIO_FORMATS,
            "quality": QUALITY_PRESETS,
            "browsers": BROWSERS,
        }

    def _cmd_locales(self, args: dict) -> dict:
        return {"available": i18n.available()}

    def _cmd_strings(self, args: dict) -> dict:
        lang = args.get("lang", i18n.DEFAULT_LANG)
        return {"lang": lang, "strings": i18n._load_all().get(lang, {})}

    def _cmd_download(self, args: dict) -> dict:
        opts = DownloadOptions(**args["options"])
        dl = Downloader(opts, log_cb=self._log_cb,
                        progress_cb=self._progress_cb, item_start_cb=self._item_start_cb)
        self._active = dl
        try:
            results = dl.download_batch(args["urls"])
        finally:
            self._active = None
        # Normalise (url, ok, err) tuples to JSON arrays for a stable contract.
        return {"results": [list(r) for r in results]}

    def _cmd_convert(self, args: dict) -> dict:
        conv = Converter(
            save_path=args["save_path"], dst_fmt=args["dst_fmt"],
            log_cb=self._log_cb, ffmpeg_bin=args.get("ffmpeg_bin") or DEFAULT_FFMPEG,
        )
        self._active = conv
        try:
            jobs = conv.convert_batch(args["files"])
        finally:
            self._active = None
        return {"jobs": [
            {"src": j.src_path, "dst": j.dst_path, "status": j.status, "error": j.error}
            for j in jobs
        ]}

    def _cmd_run_queue(self, args: dict) -> dict:
        tasks = [self._task_from_dict(t) for t in args["tasks"]]
        tq = TaskQueue(log_cb=self._log_cb, task_update_cb=self._task_update_cb,
                       ffmpeg_bin=args.get("ffmpeg_bin") or DEFAULT_FFMPEG)
        self._active = tq
        try:
            tq.run(tasks)
        finally:
            self._active = None
        return {"tasks": [
            {"kind": t.kind, "label": t.label, "status": t.status, "error": t.error}
            for t in tasks
        ]}

    def _cmd_ai_plan(self, args: dict) -> dict:
        orch = Orchestrator(args["api_key"], log_cb=self._log_cb)
        try:
            return orch.plan(args["prompt"], context=args.get("context"))
        except OrchestratorError as e:
            self._log_cb("err", "log_ai_plan_error", err=str(e))
            raise

    def _cmd_ai_summarize(self, args: dict) -> dict:
        orch = Orchestrator(args["api_key"])
        try:
            return {"text": orch.summarize(args["results"])}
        except OrchestratorError as e:
            self._log_cb("err", "log_ai_plan_error", err=str(e))
            raise

    def _cmd_stop(self, args: dict) -> dict:
        active = self._active
        if active is not None and hasattr(active, "stop"):
            active.stop()
        return {"stopping": True}

    # ── Helpers ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _task_from_dict(d: dict) -> Task:
        kind = d.get("kind")
        if kind == "download":
            return Task(kind="download", label=d.get("label", ""),
                        url=d.get("url"), options=DownloadOptions(**d["options"]))
        if kind == "convert":
            return Task(kind="convert", label=d.get("label", ""),
                        src_path=d.get("src_path"), dst_path=d.get("dst_path"))
        return Task(kind=kind or "?", label=d.get("label", ""))


def main(inp=None, out=None) -> None:
    """Run the stdio event loop. Long-running ops run on worker threads so that
    a ``stop`` request can be received and acted on mid-operation."""
    inp = inp or sys.stdin
    out = out or sys.stdout
    lock = threading.Lock()

    def emit(obj: dict) -> None:
        line = json.dumps(obj, ensure_ascii=False)
        with lock:
            out.write(line + "\n")
            out.flush()

    sidecar = Sidecar(emit)
    workers: list[threading.Thread] = []

    for raw in inp:
        raw = raw.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            emit({"id": None, "ok": False, "error": "invalid JSON"})
            continue

        cmd = req.get("cmd")
        # `stop` / `ping` are handled inline (not queued) so `stop` can interrupt.
        if cmd in ("stop", "ping"):
            emit(sidecar.dispatch(req))
            continue

        # Long-running commands run on a worker thread; response emitted when done.
        t = threading.Thread(target=lambda r=req: emit(sidecar.dispatch(r)), daemon=True)
        t.start()
        workers.append(t)
        workers = [w for w in workers if w.is_alive()]

    # Drain in-flight work before exiting so no daemon thread races the shutdown.
    for w in workers:
        w.join()


if __name__ == "__main__":
    main()
