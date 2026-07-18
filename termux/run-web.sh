#!/usr/bin/env bash
# Multimedia Downloader — web UI launcher for Android (Termux).
# Installs deps, fetches the prebuilt web UI (no Node needed), and starts the
# server. Then open the printed URL in your phone's browser.
#
#   bash termux/run-web.sh
#   PORT=8080 MMDL_DOWNLOADS=~/storage/downloads bash termux/run-web.sh
set -e
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"

if command -v pkg >/dev/null 2>&1; then          # running under Termux
  # Termux has no partial upgrades: a full upgrade must run BEFORE installing,
  # or new packages (ffmpeg/libplacebo) fail to link against the old libc++.
  yes | pkg upgrade -y || pkg upgrade -y
  pkg install -y python ffmpeg
fi
python -m pip install --upgrade --quiet flask yt-dlp

# The built web UI isn't in the git repo — fetch the prebuilt bundle once.
if [ ! -f frontend/dist/index.html ]; then
  echo "Fetching prebuilt web UI (frontend-dist.zip)…"
  curl -L -o /tmp/mmdl-dist.zip \
    "https://github.com/SpaceSquare640/Multimedia_Downloader/releases/latest/download/frontend-dist.zip"
  mkdir -p frontend && rm -rf frontend/dist
  python - <<'PY'
import zipfile
zipfile.ZipFile("/tmp/mmdl-dist.zip").extractall("frontend")
PY
fi

export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8080}"
export MMDL_DOWNLOADS="${MMDL_DOWNLOADS:-$HOME/storage/downloads}"
echo "──────────────────────────────────────────────"
echo " Open  http://$HOST:$PORT  in your phone browser"
echo " Downloads → $MMDL_DOWNLOADS"
echo "──────────────────────────────────────────────"
exec python web_app.py
