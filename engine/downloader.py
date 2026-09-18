"""
Downloader — orchestrates one or more downloads using yt-dlp.

Ported from V3.0 ``core.Downloader`` with identical behaviour and log keys.
Refactored so a single URL can be downloaded via :meth:`download_one` (used by
both :meth:`download_batch` and the AI-driven :class:`engine.queue.TaskQueue`).
"""

from __future__ import annotations

import os
import time
from typing import Iterable, Optional

import yt_dlp

from .errors import ErrorKind, classify, is_stale_tool
from .formats import (
    AUDIO_FORMATS,
    QUALITY_PRESETS,
    VIDEO_FORMATS,
    build_ydl_format_string,
    ensure_known,
    platform_headers,
)
from .options import (
    DownloadOptions,
    ItemStartCallback,
    LogCallback,
    ProgressCallback,
)

#: How many extra attempts a transient failure gets, and how long to wait
#: between them. Kept short: the delay is user-visible in the Run Log.
_MAX_RETRIES = 2
_RETRY_DELAY_S = 2


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
                self._download_one_with_retry(url, i, total)
                self._log("ok", "log_item_done", i=i, t=total)
                results.append((url, True, ""))
            except Exception as e:  # yt-dlp raises DownloadError + others
                self._log("err", "log_item_error", i=i, t=total, err=str(e))
                results.append((url, False, str(e)))

        self._log_batch_summary(results, total)
        return results

    def _log_batch_summary(
        self, results: list[tuple[str, bool, str]], total: int
    ) -> None:
        """
        Report how the batch actually ended.

        Previously this always logged ``log_all_done`` at "ok" level, so a batch
        where every item failed still showed a green checkmark. Mirrors the
        ok/fail reporting :class:`engine.queue.TaskQueue` already does.
        """
        ok = sum(1 for _, success, _ in results if success)
        fail = len(results) - ok

        if fail == 0:
            self._log("ok", "log_all_done", t=total)
        elif ok == 0:
            self._log("err", "log_all_failed", t=fail)
        else:
            self._log("warn", "log_all_done_partial", ok=ok, fail=fail, t=total)

    def _download_one_with_retry(self, url: str, i: int, total: int) -> None:
        """Retry ``download_one`` on transient errors (e.g. YouTube 403s)."""
        for attempt in range(_MAX_RETRIES + 1):
            try:
                self.download_one(url)
                return
            except Exception as e:
                is_transient = classify(e) is ErrorKind.TRANSIENT
                if not is_transient or attempt == _MAX_RETRIES or self._stop:
                    # A 403 that survives every retry is almost always a stale
                    # extractor (YouTube rotates its player), not a transient
                    # blip -- point the user at updating rather than retrying.
                    # That is the TRANSIENT -> STALE_TOOL transition: the same
                    # exception means something different once retrying failed.
                    if is_stale_tool(e):
                        self._log("warn", "log_hint_outdated", i=i, t=total)
                    raise
                # Log before sleeping: otherwise the UI sits silent for the
                # whole delay and looks frozen.
                self._log("info", "log_item_retry", i=i, t=total,
                          n=attempt + 1, max=_MAX_RETRIES)
                time.sleep(_RETRY_DELAY_S)

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

        # Validated here, in the branch that consumes them, because this is
        # where they are composed into the output template and the format
        # selector -- the same reason Converter.make_job() validates dst_fmt.
        # Only the fields this mode actually uses are checked, so a caller that
        # leaves the other mode's field blank is not punished for it.
        if o.mode == "video":
            fmt = ensure_known(o.video_fmt, VIDEO_FORMATS, "video format")
            quality = ensure_known(o.quality, QUALITY_PRESETS, "quality preset")
            return {
                **base,
                "format":              build_ydl_format_string(quality, fmt),
                "merge_output_format": fmt,
            }

        # audio mode
        return {
            **base,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   ensure_known(o.audio_fmt, AUDIO_FORMATS,
                                                 "audio format"),
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
