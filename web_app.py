"""
Standalone web backend for the V4.0/V4.1 frontend.

The desktop app runs the same Svelte frontend inside a Tauri shell, where Rust
spawns ``engine_sidecar.py`` per operation over stdio. This module gives that
*identical* frontend a real HTTP/SSE backend so it works as a deployable web app
(``python web_app.py`` → http://127.0.0.1:5000), with real yt-dlp downloads and
ffmpeg conversions — replacing the browser-only ``MockApi`` fallback.

Design: it reuses the SAME ``Sidecar`` dispatch and event protocol as the stdio
sidecar (see ``engine_sidecar.py``). Only the transport changes:

    stdio newline-JSON   →   HTTP POST (commands) + SSE stream (events)

so ``engine/`` and ``ai/orchestrator.py`` are untouched. One process-wide
``Sidecar`` handles one operation at a time (single-user model, mirroring the
desktop's ``self._active`` and V3.0's ``web_app.py``); events fan out to every
connected browser via Server-Sent Events.

Deploy notes:
    python web_app.py                       # localhost:5000
    HOST=0.0.0.0 PORT=8000 python web_app.py # LAN / server
For production behind gunicorn, use a streaming-friendly worker for the SSE
endpoint, e.g. ``gunicorn -k gthread -w 1 --threads 8 web_app:app`` (a single
worker keeps the one-op-at-a-time model and shared event bus intact).

Files produced by downloads/conversions land under ``MMDL_DOWNLOADS`` (default
``./downloads``) — a server-side directory — and are retrievable at
``/files/<name>``. In the browser, leave the save-path field blank to use it.
"""

from __future__ import annotations

import json
import os
import queue
import sys
import threading

from flask import Flask, Response, jsonify, request, send_from_directory

import i18n
from engine_sidecar import Sidecar

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(HERE, "frontend", "dist")
DOWNLOADS_DIR = os.environ.get("MMDL_DOWNLOADS", os.path.join(HERE, "downloads"))

app = Flask(__name__, static_folder=None)

# ── Event bus: fan events out to every connected SSE client ──────────────────
_subscribers: set[queue.Queue] = set()
_sub_lock = threading.Lock()


def _emit(obj: dict) -> None:
    with _sub_lock:
        subs = list(_subscribers)
    for q in subs:
        q.put(obj)


# One shared dispatcher — same command handlers as the stdio sidecar.
_sidecar = Sidecar(_emit)


def _dispatch(cmd: str, args: dict):
    """Run one command through the shared Sidecar and unwrap its response."""
    resp = _sidecar.dispatch({"id": cmd, "cmd": cmd, "args": args})
    if resp.get("ok"):
        return jsonify(resp.get("result"))
    return jsonify({"error": resp.get("error", "error")}), 500


def _save_path(value) -> str:
    """Resolve a save/output dir: use the caller's if given, else the server
    downloads dir. Web clients can't browse the server's filesystem, so a blank
    field means 'put it in the server's downloads folder'."""
    p = (value or "").strip()
    if not p:
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        return DOWNLOADS_DIR
    return p


# ── Command endpoints (mirror the Rust IPC commands in src-tauri/main.rs) ─────
@app.get("/api/formats")
def api_formats():
    return _dispatch("formats", {})


@app.get("/api/locales")
def api_locales():
    # Frontend expects the {code: name} map directly (Rust unwraps .available).
    resp = _sidecar.dispatch({"id": "locales", "cmd": "locales", "args": {}})
    return jsonify(resp.get("result", {}).get("available", {}))


@app.post("/api/download")
def api_download():
    a = request.get_json(force=True) or {}
    args = {
        "urls": a.get("urls", []),
        "options": {
            "save_path": _save_path(a.get("save_path")),
            "mode": a.get("mode", "video"),
            "video_fmt": a.get("video_fmt", "mp4"),
            "audio_fmt": a.get("audio_fmt", "mp3"),
            "quality": a.get("quality", "best"),
            "browser": a.get("browser", "none"),
        },
    }
    return _dispatch("download", args)


@app.post("/api/convert")
def api_convert():
    a = request.get_json(force=True) or {}
    args = {
        "files": a.get("files", []),
        "dst_fmt": a.get("dst_fmt", "mp4"),
        "save_path": _save_path(a.get("save_path")),
    }
    return _dispatch("convert", args)


@app.post("/api/run_queue")
def api_run_queue():
    a = request.get_json(force=True) or {}
    return _dispatch("run_queue", {"tasks": a.get("tasks", [])})


@app.post("/api/ai_plan")
def api_ai_plan():
    a = request.get_json(force=True) or {}
    return _dispatch("ai_plan", {
        "api_key": a.get("api_key", ""),
        "prompt": a.get("prompt", ""),
        "context": a.get("context"),
    })


@app.post("/api/stop")
def api_stop():
    return _dispatch("stop", {})


# ── SSE event stream ─────────────────────────────────────────────────────────
@app.get("/events")
def events():
    def stream():
        q: queue.Queue = queue.Queue()
        with _sub_lock:
            _subscribers.add(q)
        try:
            yield ": connected\n\n"  # open the stream immediately
            while True:
                obj = q.get()
                yield f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"
        finally:
            with _sub_lock:
                _subscribers.discard(q)

    return Response(stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # disable proxy buffering (nginx)
        "Connection": "keep-alive",
    })


# ── Produced-file retrieval ──────────────────────────────────────────────────
@app.get("/files/<path:name>")
def files(name):
    return send_from_directory(DOWNLOADS_DIR, name, as_attachment=True)


# ── Static frontend (built Svelte app) ───────────────────────────────────────
@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.get("/<path:path>")
def static_proxy(path):
    full = os.path.join(FRONTEND_DIST, path)
    if os.path.isfile(full):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")  # SPA fallback


def main() -> None:
    if not os.path.isdir(FRONTEND_DIST):
        sys.stderr.write(
            f"[web_app] frontend not built at {FRONTEND_DIST}\n"
            "  build it first:  npm run build:frontend:web\n"
        )
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    lang_note = ", ".join(i18n.available().keys())
    sys.stderr.write(f"[web_app] serving on http://{host}:{port}  (langs: {lang_note})\n")
    # threaded=True so the SSE stream and command requests run concurrently.
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
