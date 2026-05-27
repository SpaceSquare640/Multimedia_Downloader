"""
Core download / conversion logic — UI-agnostic.

This module wraps yt-dlp and ffmpeg behind a clean callback-based API so that
the desktop GUI (Multimedia_Downloader.py) and the web app (web_app.py) can
share identical behaviour without duplicating logic.

Design
------
*  No tkinter, no Flask — only stdlib + yt_dlp.
*  All progress / log events are dispatched through optional callbacks so the
   caller chooses whether to forward them to a queue, an SSE stream, a print
   statement, or nothing at all.
*  A cooperative ``stop()`` flag aborts batch operations between items.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

import yt_dlp


# ─────────────────────────────────────────────────────────────────────────────
#  Format catalogue
# ─────────────────────────────────────────────────────────────────────────────

VIDEO_FORMATS: list[str] = [
    "mp4", "mkv", "mov", "avi", "webm",
    "flv", "wmv", "ts",  "m4v", "3gp",
]

AUDIO_FORMATS: list[str] = [
    "mp3", "flac", "aac", "wav",
    "ogg", "m4a", "opus", "wma",
]

QUALITY_PRESETS: list[str] = ["best", "1080p", "720p", "480p", "360p", "worst"]

BROWSERS: list[str] = [
    "none", "chrome", "firefox", "edge",
    "safari", "brave", "opera", "chromium",
]


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def format_filesize(size_bytes: int) -> str:
    """
    Convert byte count to a human-readable string (KB, MB, or GB).

    Uses 1 MiB / 1 GiB as boundaries (>=) so that exactly 1 MiB displays
    as "1.0 MB" rather than "1024.0 KB".
    """
    if size_bytes >= 1_073_741_824:        # 1 GiB
        return f"{size_bytes / 1_073_741_824:.2f} GB"
    if size_bytes >= 1_048_576:            # 1 MiB
        return f"{size_bytes / 1_048_576:.1f} MB"
    return f"{size_bytes / 1024:.1f} KB"


def build_ydl_format_string(quality: str, fmt: str) -> str:
    """
    Build a yt-dlp ``format`` selection string from a quality preset
    and a target container format.

    yt-dlp format syntax notes::

        bestvideo[...]   = best video stream (optionally height-capped)
        bestaudio        = best audio stream
        /best            = fallback: use best combined stream if separate unavailable
    """
    if quality == "best":
        return f"bestvideo[ext={fmt}]+bestaudio/best[ext={fmt}]/best"
    if quality == "worst":
        return "worstvideo+worstaudio/worst"
    height = quality.replace("p", "")
    return (
        f"bestvideo[height<={height}]+bestaudio"
        f"/best[height<={height}]/best"
    )


def is_douyin(url: str) -> bool:
    return "douyin.com" in url or "v.douyin.com" in url


def is_tiktok(url: str) -> bool:
    return "tiktok.com" in url


# ─────────────────────────────────────────────────────────────────────────────
#  DownloadOptions — the immutable settings for one batch
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DownloadOptions:
    """
    Settings for a download batch.

    Attributes
    ----------
    save_path : str
        Destination directory (must already exist).
    mode : str
        Either ``"video"`` or ``"audio"``.
    video_fmt : str
        Target container when mode is ``"video"``.
    audio_fmt : str
        Target codec when mode is ``"audio"``.
    quality : str
        One of :data:`QUALITY_PRESETS`.
    cookie_file : Optional[str]
        Path to a Netscape ``cookies.txt`` file (takes priority over browser).
    browser : Optional[str]
        Browser name to read cookies from. ``"none"`` or ``None`` disables.
    """
    save_path:   str
    mode:        str  = "video"
    video_fmt:   str  = "mp4"
    audio_fmt:   str  = "mp3"
    quality:     str  = "best"
    cookie_file: Optional[str] = None
    browser:     Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
#  Callbacks — small typed aliases for clarity
# ─────────────────────────────────────────────────────────────────────────────

#: ``(level, key, **fmt) -> None`` — level is one of "info", "ok", "warn", "err"
LogCallback = Callable[..., None]

#: ``(percent, speed_str, eta_str) -> None``
ProgressCallback = Callable[[float, str, str], None]

#: ``(index, total, url) -> None``
ItemStartCallback = Callable[[int, int, str], None]


# ─────────────────────────────────────────────────────────────────────────────
#  Downloader — orchestrates one or more downloads using yt-dlp
# ─────────────────────────────────────────────────────────────────────────────

class Downloader:
    """
    Stateful download orchestrator.

    The instance carries a cooperative ``_stop`` flag so a batch can be aborted
    cleanly between items. All side-effects (progress, log lines) are reported
    through the callbacks passed in at construction.

    Callbacks may be ``None``; ``Downloader`` checks before calling.
    """

    def __init__(
        self,
        options:        DownloadOptions,
        log_cb:         Optional[LogCallback]         = None,
        progress_cb:    Optional[ProgressCallback]    = None,
        item_start_cb:  Optional[ItemStartCallback]   = None,
    ) -> None:
        self.opts          = options
        self.log_cb        = log_cb
        self.progress_cb   = progress_cb
        self.item_start_cb = item_start_cb
        self._stop         = False

    # ── Public ────────────────────────────────────────────────────────────────
    def stop(self) -> None:
        """Request cooperative cancellation. The current item finishes first."""
        self._stop = True

    def download_batch(self, urls: Iterable[str]) -> list[tuple[str, bool, str]]:
        """
        Download every URL sequentially.

        Returns a list of ``(url, success, error_message)`` triples.
        """
        urls = list(urls)
        total = len(urls)
        results: list[tuple[str, bool, str]] = []
        self._stop = False

        self._log("info", "log_start_batch", n=total)

        for i, url in enumerate(urls, start=1):
            if self._stop:
                self._log("warn", "log_stopped_dl")
                break

            if self.item_start_cb:
                self.item_start_cb(i, total, url)
            self._log("info", "log_item_downloading", i=i, t=total, url=url)

            try:
                self._download_one(url)
                self._log("ok", "log_item_done", i=i, t=total)
                results.append((url, True, ""))
            except Exception as e:  # yt-dlp raises DownloadError + others
                self._log("err", "log_item_error", i=i, t=total, err=str(e))
                results.append((url, False, str(e)))

        self._log("ok", "log_all_done", t=total)
        return results

    # ── Private ───────────────────────────────────────────────────────────────
    def _download_one(self, url: str) -> None:
        opts = self._build_ydl_opts(url)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def _build_ydl_opts(self, url: str) -> dict:
        o = self.opts

        # Per-platform headers — required for Douyin and TikTok to avoid 403s.
        headers: dict[str, str] = {}
        if is_douyin(url):
            headers = {
                "Referer":    "https://www.douyin.com/",
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/17.0 Mobile/15E148 Safari/604.1"
                ),
            }
        elif is_tiktok(url):
            headers = {
                "Referer":    "https://www.tiktok.com/",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            }

        base: dict = {
            "outtmpl":        os.path.join(o.save_path, "%(title)s.%(ext)s"),
            "quiet":          True,
            "no_warnings":    True,
            "progress_hooks": [self._ydl_hook],
        }

        # Cookies: file first (more reliable), then browser.
        if o.cookie_file and os.path.isfile(o.cookie_file):
            base["cookiefile"] = o.cookie_file
            self._log("info", "log_cookie_file", name=os.path.basename(o.cookie_file))
        elif o.browser and o.browser != "none":
            base["cookiesfrombrowser"] = (o.browser, None, None, None)
            self._log("info", "log_cookie_browser", browser=o.browser)

        if headers:
            base["http_headers"] = headers

        if o.mode == "video":
            fmt = o.video_fmt
            return {
                **base,
                "format":              build_ydl_format_string(o.quality, fmt),
                "merge_output_format": fmt,
            }

        # audio mode
        return {
            **base,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   o.audio_fmt,
                "preferredquality": "192",
            }],
        }

    def _ydl_hook(self, d: dict) -> None:
        """yt-dlp progress hook — fans out to the registered progress callback."""
        if d["status"] == "downloading" and self.progress_cb:
            try:
                pct_str = d.get("_percent_str", "0%").strip().replace("%", "")
                pct     = float(pct_str)
                speed   = d.get("_speed_str", "--").strip()
                eta     = d.get("_eta_str",   "--").strip()
                self.progress_cb(pct, speed, eta)
            except (ValueError, TypeError):
                pass  # silently skip unparseable progress strings
        elif d["status"] == "finished" and self.progress_cb:
            self.progress_cb(100.0, "--", "--")

    # ── Log dispatch ──────────────────────────────────────────────────────────
    def _log(self, level: str, key: str, **fmt) -> None:
        if self.log_cb:
            self.log_cb(level, key, **fmt)


# ─────────────────────────────────────────────────────────────────────────────
#  Converter — wraps ffmpeg for batch transcoding
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ConvertJob:
    """One file in a conversion queue."""
    src_path:  str
    dst_path:  str
    status:    str = "pending"   # pending | converting | done | error | no_ffmpeg
    error:     str = ""


class Converter:
    """
    Sequentially transcode files using ``ffmpeg``.

    Like :class:`Downloader`, exposes a stop flag and forwards progress through
    optional callbacks.

    Callbacks
    ---------
    log_cb(level, key, **fmt)
        Forwarded log lines (level: ``info`` | ``ok`` | ``warn`` | ``err``).
    job_update_cb(job)
        Called whenever a job's status changes.
    """

    def __init__(
        self,
        save_path:    str,
        dst_fmt:      str,
        log_cb:       Optional[LogCallback]              = None,
        job_update_cb: Optional[Callable[[ConvertJob], None]] = None,
    ) -> None:
        self.save_path     = save_path
        self.dst_fmt       = dst_fmt
        self.log_cb        = log_cb
        self.job_update_cb = job_update_cb
        self._stop         = False

    def stop(self) -> None:
        self._stop = True

    def convert_batch(self, src_files: Iterable[str]) -> list[ConvertJob]:
        """Run ffmpeg on each file. Returns the list of jobs with final status."""
        jobs: list[ConvertJob] = []
        for src in src_files:
            base = os.path.splitext(os.path.basename(src))[0]
            jobs.append(ConvertJob(
                src_path = src,
                dst_path = os.path.join(self.save_path, f"{base}.{self.dst_fmt}"),
            ))

        total = len(jobs)
        self._stop = False

        for i, job in enumerate(jobs, start=1):
            if self._stop:
                self._log("warn", "log_convert_stopped")
                break

            self._log("info", "log_convert_start",
                      i=i, t=total,
                      src=os.path.basename(job.src_path),
                      dst=os.path.basename(job.dst_path))
            self._set_status(job, "converting")

            try:
                result = subprocess.run(
                    ["ffmpeg", "-y", "-i", job.src_path, "-loglevel", "error", job.dst_path],
                    capture_output=True, text=True,
                )
                if result.returncode == 0:
                    self._log("ok", "log_convert_done",
                              i=i, t=total, name=os.path.basename(job.dst_path))
                    self._set_status(job, "done")
                else:
                    raise RuntimeError(result.stderr[:300] or "ffmpeg error (no output)")

            except FileNotFoundError:
                self._log("err", "log_no_ffmpeg", i=i, t=total)
                self._set_status(job, "no_ffmpeg", error="ffmpeg not found")

            except Exception as e:
                self._log("err", "log_convert_error", i=i, t=total, err=str(e))
                self._set_status(job, "error", error=str(e))

        self._log("ok", "log_all_converted", t=total)
        return jobs

    # ── Internal ──────────────────────────────────────────────────────────────
    def _set_status(self, job: ConvertJob, status: str, error: str = "") -> None:
        job.status = status
        if error:
            job.error = error
        if self.job_update_cb:
            self.job_update_cb(job)

    def _log(self, level: str, key: str, **fmt) -> None:
        if self.log_cb:
            self.log_cb(level, key, **fmt)
