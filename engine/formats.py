"""
Format catalogue and pure helper functions.

This module has **no** yt-dlp / ffmpeg dependency — only stdlib — so it is
trivially unit-testable and safe to import from anywhere (frontend bridge,
AI planner, tests). Ported verbatim from V3.0 ``core.py`` behaviour.
"""

from __future__ import annotations

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


def platform_headers(url: str) -> dict[str, str]:
    """
    Per-platform HTTP headers required to avoid 403s.

    Douyin and TikTok reject requests without a matching Referer / User-Agent.
    Returns an empty dict for every other site.
    """
    if is_douyin(url):
        return {
            "Referer":    "https://www.douyin.com/",
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
        }
    if is_tiktok(url):
        return {
            "Referer":    "https://www.tiktok.com/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
    return {}
