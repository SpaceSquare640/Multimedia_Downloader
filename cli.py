#!/usr/bin/env python3
"""
Multimedia Downloader — command-line interface.

A thin terminal wrapper around the *same* engine the desktop and web apps use
(yt-dlp + ffmpeg). No GUI, no Node, no Rust — just Python + ffmpeg — so it runs
anywhere Python does, including headless servers and Android via Termux.

Setup (any platform):
    pip install yt-dlp            # engine dependency
    # ffmpeg must be on PATH (Termux: pkg install ffmpeg)

Examples:
    python cli.py download "https://youtu.be/XXXX" -o ~/dl -f mp4 -q 720p
    python cli.py download URL1 URL2 --audio --audio-format mp3
    python cli.py convert clip.mkv movie.mov -o ~/out -f mp4
    python cli.py formats
    python cli.py --lang zh_tw download "https://..."
"""
from __future__ import annotations

import argparse
import os
import sys

# Make the bundled engine importable no matter where cli.py is invoked from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import i18n
from engine import (
    AUDIO_FORMATS,
    BROWSERS,
    QUALITY_PRESETS,
    VIDEO_FORMATS,
    Converter,
    DownloadOptions,
    Downloader,
)

_ICON = {"info": "·", "ok": "✓", "warn": "!", "err": "✗"}


def _make_logger(tr: "i18n.Translator"):
    def log(level: str, key: str, **fmt) -> None:
        print(f" {_ICON.get(level, '·')} {tr.t(key, **fmt)}")
    return log


def cmd_download(args, log) -> int:
    os.makedirs(args.output, exist_ok=True)
    opts = DownloadOptions(
        save_path=args.output,
        mode="audio" if args.audio else "video",
        video_fmt=args.format,
        audio_fmt=args.audio_format,
        quality=args.quality,
        cookie_file=args.cookies,
        browser=None if args.browser == "none" else args.browser,
    )
    # yt-dlp prints its own progress bar; no extra progress_cb needed here.
    dl = Downloader(opts, log_cb=log)
    results = dl.download_batch(args.urls)
    ok = sum(1 for _, success, _ in results if success)
    print(f"\nDone: {ok}/{len(results)} succeeded. Files in {os.path.abspath(args.output)}")
    return 0 if ok == len(results) else 1


def cmd_convert(args, log) -> int:
    os.makedirs(args.output, exist_ok=True)
    conv = Converter(save_path=args.output, dst_fmt=args.format, log_cb=log, ffmpeg_bin=args.ffmpeg)
    jobs = conv.convert_batch(args.files)
    ok = sum(1 for j in jobs if j.status == "done")
    print(f"Done: {ok}/{len(jobs)} converted. Files in {os.path.abspath(args.output)}")
    return 0 if ok == len(jobs) else 1


def cmd_formats(args, log) -> int:
    print("Video containers :", "  ".join(VIDEO_FORMATS))
    print("Audio formats    :", "  ".join(AUDIO_FORMATS))
    print("Quality presets  :", "  ".join(QUALITY_PRESETS))
    print("Cookie browsers  :", "  ".join(BROWSERS))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mmdl",
        description="Multimedia Downloader CLI — download & convert with yt-dlp + ffmpeg.",
    )
    p.add_argument("--lang", default="en", help="message language: en / zh_tw / zh_cn")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download", help="download video/audio from one or more URLs")
    d.add_argument("urls", nargs="+", help="one or more URLs (500+ sites via yt-dlp)")
    d.add_argument("-o", "--output", default=".", help="output directory (default: current dir)")
    d.add_argument("-f", "--format", default="mp4", choices=VIDEO_FORMATS, help="video container")
    d.add_argument("-q", "--quality", default="best", choices=QUALITY_PRESETS, help="video quality")
    d.add_argument("--audio", action="store_true", help="extract audio instead of video")
    d.add_argument("--audio-format", default="mp3", choices=AUDIO_FORMATS, help="audio format (with --audio)")
    d.add_argument("--browser", default="none", choices=BROWSERS, help="read login cookies from this browser")
    d.add_argument("--cookies", help="path to a Netscape cookies.txt file (overrides --browser)")
    d.set_defaults(func=cmd_download)

    c = sub.add_parser("convert", help="convert local media files with ffmpeg")
    c.add_argument("files", nargs="+", help="input files")
    c.add_argument("-o", "--output", default=".", help="output directory (default: current dir)")
    c.add_argument("-f", "--format", default="mp4", choices=VIDEO_FORMATS + AUDIO_FORMATS, help="target format")
    c.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg binary (default: 'ffmpeg' on PATH)")
    c.set_defaults(func=cmd_convert)

    f = sub.add_parser("formats", help="list supported formats / quality / browsers")
    f.set_defaults(func=cmd_formats)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    log = _make_logger(i18n.Translator(args.lang))
    try:
        return args.func(args, log)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
