"""
Data types shared across the engine: settings dataclasses and callback aliases.

Kept dependency-free (stdlib only) so both the download/convert modules and the
AI planner can import them without pulling in yt-dlp/ffmpeg.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


# ─────────────────────────────────────────────────────────────────────────────
#  DownloadOptions — the settings for one download (or download batch)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DownloadOptions:
    """
    Settings for a download.

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
        One of :data:`engine.formats.QUALITY_PRESETS`.
    cookie_file : Optional[str]
        Path to a Netscape ``cookies.txt`` file (takes priority over browser).
    browser : Optional[str]
        Browser name to read cookies from. ``"none"`` or ``None`` disables.
    """
    save_path:   str
    mode:        str = "video"
    video_fmt:   str = "mp4"
    audio_fmt:   str = "mp3"
    quality:     str = "best"
    cookie_file: Optional[str] = None
    browser:     Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
#  ConvertJob — one file in a conversion queue
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ConvertJob:
    """One file in a conversion queue."""
    src_path: str
    dst_path: str
    status:   str = "pending"   # pending | converting | done | error | no_ffmpeg
    error:    str = ""


# ─────────────────────────────────────────────────────────────────────────────
#  Callback type aliases — small typed hints for clarity
# ─────────────────────────────────────────────────────────────────────────────

#: ``(level, key, **fmt) -> None`` — level is one of "info", "ok", "warn", "err"
LogCallback = Callable[..., None]

#: ``(percent, speed_str, eta_str) -> None``
ProgressCallback = Callable[[float, str, str], None]

#: ``(index, total, url) -> None``
ItemStartCallback = Callable[[int, int, str], None]

#: ``(job) -> None`` — a ConvertJob whose status just changed
JobUpdateCallback = Callable[["ConvertJob"], None]
