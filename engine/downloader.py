"""
Downloader — orchestrates one or more downloads using yt-dlp.

Ported from V3.0 ``core.Downloader`` with identical behaviour and log keys.
Refactored so a single URL can be downloaded via :meth:`download_one` (used by
both :meth:`download_batch` and the AI-driven :class:`engine.queue.TaskQueue`).
"""

from __future__ import annotations

import os
from typing import Iterable, Optional

import yt_dlp

from .formats import build_ydl_format_string, platform_headers
from .options import (
    DownloadOptions,
    ItemStartCallback,
    LogCallback,
    ProgressCallback,
)


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
        options:       DownloadOptions,
        log_cb:        Optional[LogCallback]       = None,
        progress_cb:   Optional[ProgressCallback]  = None,
        item_start_cb: Optional[ItemStartCallback] = None,
    ) -> None:
        self.opts          = options
        self.log_cb        = log_cb
        self.progress_cb   = progress_cb
        self.item_start_cb = item_start_cb
        self._stop         = False
        # yt-dlp expands a playlist URL into all its entries on its own (no
        # option here restricts it) -- this only tracks that expansion so we
        # can log "item i/n" as it moves between entries; it does not change
        # what gets downloaded.
        self._playlist_index_logged: Optional[int] = None

    # ── Public ──────────────────────────────────────────────────────────────
    def stop(self) -> None:
        """Request cooperative cancellation. The current item finishes first."""
        self._stop = True

    def download_one(self, url: str) -> None:
        """
        Download a single URL. Raises on failure (yt-dlp ``DownloadError`` etc.).

        This is the atomic unit reused by :meth:`download_batch` and the task
        queue; it does not catch exceptions so callers can decide how to report.
        """
        self._playlist_index_logged = None
        opts = self._build_ydl_opts(url)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

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
                self.download_one(url)
                self._log("ok", "log_item_done", i=i, t=total)
                results.append((url, True, ""))
            except Exception as e:  # yt-dlp raises DownloadError + others
                self._log("err", "log_item_error", i=i, t=total, err=str(e))
                results.append((url, False, str(e)))

        self._log("ok", "log_all_done", t=total)
        return results

    # ── Private ─────────────────────────────────────────────────────────────
    def _build_ydl_opts(self, url: str) -> dict:
        o = self.opts
        headers = platform_headers(url)

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
        info = d.get("info_dict") or {}
        n_entries, idx = info.get("n_entries"), info.get("playlist_index")
        if n_entries and idx and idx != self._playlist_index_logged:
            self._playlist_index_logged = idx
            self._log("info", "log_playlist_item", i=idx, t=n_entries,
                      title=info.get("title") or info.get("id") or "")

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

    # ── Log dispatch ────────────────────────────────────────────────────────
    def _log(self, level: str, key: str, **fmt) -> None:
        if self.log_cb:
            self.log_cb(level, key, **fmt)
