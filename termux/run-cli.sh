#!/usr/bin/env bash
# Multimedia Downloader — CLI launcher for Android (Termux) or any POSIX shell.
# Installs the minimal deps (Termux only) then runs cli.py with your arguments.
#
#   bash termux/run-cli.sh download "https://youtu.be/XXXX" -o ~/storage/downloads -f mp4
#   bash termux/run-cli.sh download "https://..." --audio --audio-format mp3
#   bash termux/run-cli.sh formats
set -e
here="$(cd "$(dirname "$0")/.." && pwd)"
if command -v pkg >/dev/null 2>&1; then          # running under Termux
  # Termux has no partial upgrades: a full upgrade must run BEFORE installing,
  # or new packages (ffmpeg/libplacebo) fail to link against the old libc++.
  yes | pkg upgrade -y || pkg upgrade -y
  pkg install -y python ffmpeg
fi
python -m pip install --upgrade --quiet yt-dlp
exec python "$here/cli.py" "$@"
