"""
Multimedia Downloader V4.0 — download / conversion engine (Python sidecar).

UI-agnostic, callback-based engine ported and modularised from V3.0 ``core.py``.
No tkinter, no Flask — stdlib + yt_dlp + ffmpeg (external binary) only. Runs as a
Tauri sidecar; the frontend reaches it over IPC.

Modules
-------
formats     format catalogue + pure helpers (no yt-dlp/ffmpeg dependency)
options     DownloadOptions / ConvertJob dataclasses + callback type aliases
downloader  Downloader (yt-dlp)
converter   Converter (ffmpeg)
queue       Task / TaskQueue — mixed download+convert batches for the AI planner

The names below form the stable public API; import from ``engine`` directly:

    from engine import Downloader, Converter, DownloadOptions, TaskQueue
"""

from __future__ import annotations

__version__ = "4.0.0-dev"

from .formats import (
    AUDIO_FORMATS,
    BROWSERS,
    QUALITY_PRESETS,
    VIDEO_FORMATS,
    build_ydl_format_string,
    format_filesize,
    is_douyin,
    is_tiktok,
    platform_headers,
)
from .options import (
    ConvertJob,
    DownloadOptions,
    ItemStartCallback,
    JobUpdateCallback,
    LogCallback,
    ProgressCallback,
)
from .downloader import Downloader
from .converter import Converter
from .queue import (
    CONVERT,
    DOWNLOAD,
    Task,
    TaskQueue,
    TaskUpdateCallback,
    convert_task,
    download_task,
)

__all__ = [
    "__version__",
    # formats
    "VIDEO_FORMATS", "AUDIO_FORMATS", "QUALITY_PRESETS", "BROWSERS",
    "format_filesize", "build_ydl_format_string",
    "is_douyin", "is_tiktok", "platform_headers",
    # options / types
    "DownloadOptions", "ConvertJob",
    "LogCallback", "ProgressCallback", "ItemStartCallback", "JobUpdateCallback",
    # engine classes
    "Downloader", "Converter",
    # queue
    "Task", "TaskQueue", "TaskUpdateCallback",
    "download_task", "convert_task", "DOWNLOAD", "CONVERT",
]
