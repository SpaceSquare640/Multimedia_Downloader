#!/usr/bin/env python3
# =============================================================================
#  Multimedia Downloader — Web App
#  Version : 3.0
#
#  A Flask web server that exposes the same download / convert engine as the
#  desktop GUI through a clean browser-based UI.  Designed to be run two ways:
#
#  1.  LOCAL  — ``python web_app.py``     →  http://127.0.0.1:5000
#  2.  ONLINE — deploy to any WSGI host (Render, Railway, Fly.io, your VPS).
#               Set ``HOST=0.0.0.0`` and ``PORT=$PORT`` in the platform's env.
#
#  The downloader's destination folder is the local ``downloads/`` directory
#  next to this script. Finished files are then served by Flask so clients
#  can download them.
# =============================================================================

from __future__ import annotations

import os
import secrets
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import (
    Flask, Response, abort, jsonify, redirect, render_template,
    request, send_from_directory, session, url_for,
)

from core import (
    AUDIO_FORMATS, BROWSERS, QUALITY_PRESETS, VIDEO_FORMATS,
    Downloader, DownloadOptions,
)
from i18n import DEFAULT_LANG, LANG_DISPLAY, STRINGS, Translator


# ─────────────────────────────────────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR     = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Job model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Job:
    """One download submitted by a web client."""
    id:          str                       = field(default_factory=lambda: uuid.uuid4().hex[:12])
    url:         str                       = ""
    status:      str                       = "pending"        # pending|running|done|error|stopped
    progress:    float                     = 0.0
    speed:       str                       = "--"
    eta:         str                       = "--"
    filename:    Optional[str]             = None
    error:       Optional[str]             = None
    created_at:  str                       = field(default_factory=lambda: datetime.now().isoformat())
    log:         list[dict]                = field(default_factory=list)

    def public(self) -> dict:
        return {
            "id":         self.id,
            "url":        self.url,
            "status":     self.status,
            "progress":   self.progress,
            "speed":      self.speed,
            "eta":        self.eta,
            "filename":   self.filename,
            "error":      self.error,
            "created_at": self.created_at,
            "log":        self.log[-40:],          # cap log length
        }


# ─────────────────────────────────────────────────────────────────────────────
#  JobManager — singleton, thread-safe
# ─────────────────────────────────────────────────────────────────────────────

class JobManager:
    """
    Keeps an in-memory registry of jobs and runs them sequentially in a single
    worker thread (one job at a time keeps yt-dlp output predictable and
    bandwidth fair across submitters).
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job]        = {}
        self._lock                        = threading.Lock()
        self._queue: list[str]            = []
        self._current: Optional[Downloader] = None
        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()

    # ── Public API ────────────────────────────────────────────────────────────
    def submit(self, urls: list[str], opts: DownloadOptions) -> list[Job]:
        created: list[Job] = []
        with self._lock:
            for u in urls:
                job = Job(url=u)
                self._jobs[job.id] = job
                self._queue.append(job.id)
                # Stash options on the job so the worker can read them later.
                job._opts = opts    # type: ignore[attr-defined]
                created.append(job)
        return created

    def all(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def stop_current(self) -> bool:
        if self._current is not None:
            self._current.stop()
            return True
        return False

    def clear_completed(self) -> int:
        with self._lock:
            done_ids = [jid for jid, j in self._jobs.items()
                        if j.status in ("done", "error", "stopped")]
            for jid in done_ids:
                self._jobs.pop(jid, None)
            return len(done_ids)

    # ── Worker thread ─────────────────────────────────────────────────────────
    def _run_loop(self) -> None:
        import time
        while True:
            job_id = None
            with self._lock:
                if self._queue:
                    job_id = self._queue.pop(0)
            if job_id is None:
                time.sleep(0.5)
                continue
            with self._lock:
                job = self._jobs.get(job_id)
            if job is None:
                continue
            self._run_job(job)

    def _run_job(self, job: Job) -> None:
        opts: DownloadOptions = job._opts          # type: ignore[attr-defined]
        job.status = "running"

        def _log(level: str, key: str, **fmt) -> None:
            # Use English for server-side log capture (clients translate via key).
            msg = STRINGS[DEFAULT_LANG].get(key, key).format(**fmt) if fmt else \
                  STRINGS[DEFAULT_LANG].get(key, key)
            job.log.append({
                "ts":    datetime.now().strftime("%H:%M:%S"),
                "level": level,
                "key":   key,
                "fmt":   fmt,
                "msg":   msg,
            })

        def _progress(pct: float, speed: str, eta: str) -> None:
            job.progress = pct
            job.speed    = speed
            job.eta      = eta

        downloader = Downloader(opts, log_cb=_log, progress_cb=_progress)
        self._current = downloader

        try:
            # Snapshot directory contents so we can identify the new file.
            before = {p.name for p in DOWNLOAD_DIR.iterdir() if p.is_file()}

            results = downloader.download_batch([job.url])

            after = {p.name for p in DOWNLOAD_DIR.iterdir() if p.is_file()}
            new_files = list(after - before)

            ok = results and results[0][1]
            if ok:
                job.status   = "done"
                job.progress = 100.0
                if new_files:
                    # Pick the largest new file — handles temp + final stream merges.
                    new_files.sort(
                        key=lambda f: (DOWNLOAD_DIR / f).stat().st_size,
                        reverse=True,
                    )
                    job.filename = new_files[0]
            else:
                job.status = "stopped" if downloader._stop else "error"
                job.error  = results[0][2] if results else "unknown error"

        except Exception as e:
            job.status = "error"
            job.error  = str(e)

        finally:
            self._current = None


JOBS = JobManager()


# ─────────────────────────────────────────────────────────────────────────────
#  Flask app
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET", secrets.token_hex(16))


def current_lang() -> str:
    """Return the language stored in the session, defaulting to English."""
    code = session.get("lang", DEFAULT_LANG)
    return code if code in STRINGS else DEFAULT_LANG


# ── Page routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    tr = Translator(current_lang())
    return render_template(
        "index.html",
        t            = tr,
        lang_code    = tr.lang,
        lang_display = LANG_DISPLAY,
        video_fmts   = VIDEO_FORMATS,
        audio_fmts   = AUDIO_FORMATS,
        qualities    = QUALITY_PRESETS,
        browsers     = BROWSERS,
    )


@app.route("/lang/<code>")
def set_lang(code):
    if code in STRINGS:
        session["lang"] = code
    return redirect(request.referrer or url_for("index"))


# ── API routes ────────────────────────────────────────────────────────────────

@app.post("/api/jobs")
def api_submit_jobs():
    data = request.get_json(silent=True) or {}
    urls = [u.strip() for u in (data.get("urls") or "").splitlines() if u.strip()]
    if not urls:
        return jsonify(error="No URLs supplied"), 400

    opts = DownloadOptions(
        save_path   = str(DOWNLOAD_DIR),
        mode        = data.get("mode", "video"),
        video_fmt   = data.get("video_fmt", "mp4"),
        audio_fmt   = data.get("audio_fmt", "mp3"),
        quality     = data.get("quality", "best"),
        cookie_file = None,
        browser     = data.get("browser") if data.get("browser") != "none" else None,
    )
    jobs = JOBS.submit(urls, opts)
    return jsonify(jobs=[j.public() for j in jobs])


@app.get("/api/jobs")
def api_list_jobs():
    return jsonify(jobs=[j.public() for j in JOBS.all()])


@app.get("/api/jobs/<job_id>")
def api_get_job(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify(error="not found"), 404
    return jsonify(job=job.public())


@app.post("/api/stop")
def api_stop_current():
    stopped = JOBS.stop_current()
    return jsonify(stopped=stopped)


@app.post("/api/clear")
def api_clear_completed():
    n = JOBS.clear_completed()
    return jsonify(cleared=n)


@app.get("/api/strings/<code>")
def api_strings(code):
    """Return the translation table for the client-side script."""
    if code not in STRINGS:
        code = DEFAULT_LANG
    return jsonify(strings=STRINGS[code], lang=code)


@app.get("/files/<path:filename>")
def serve_file(filename):
    # Reject any path-traversal attempt by using only the basename.
    safe = os.path.basename(filename)
    if not (DOWNLOAD_DIR / safe).exists():
        abort(404)
    return send_from_directory(str(DOWNLOAD_DIR), safe, as_attachment=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    host  = os.environ.get("HOST", "127.0.0.1")
    port  = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "0") == "1"
    print(f"[OK] Multimedia Downloader Web — http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
