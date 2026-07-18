# Running on Android via Termux

The desktop app is a native binary and does **not** run on Android — but the
engine underneath it is pure Python (yt-dlp + ffmpeg), and both are available
in [Termux](https://termux.dev). So you can run Multimedia Downloader on your
phone from a terminal, either as a **CLI** or as the **web UI** in your browser.

> Install Termux from **F-Droid** or **GitHub**, not the Play Store (that build
> is outdated). Optional but recommended: `termux-setup-storage` (grants access
> to `~/storage/downloads` so files land in your normal Downloads folder).

## One-time: get the code

```bash
pkg install -y git
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
```

## Option A — CLI (lightest)

```bash
bash termux/run-cli.sh download "https://youtu.be/XXXX" -o ~/storage/downloads -f mp4 -q 720p
bash termux/run-cli.sh download "https://..." --audio --audio-format mp3
bash termux/run-cli.sh convert clip.mkv -o ~/storage/downloads -f mp4
bash termux/run-cli.sh formats
```

The script installs `python` + `ffmpeg` + `yt-dlp` on first run, then calls
[`cli.py`](../cli.py). You can also run `python cli.py --help` directly once the
deps are installed. Add `--lang zh_tw` (or `zh_cn`) for localized messages.

## Option B — Web UI in your browser

```bash
bash termux/run-web.sh
# then open the printed URL, e.g. http://127.0.0.1:8080, in your phone browser
```

This installs deps, downloads the prebuilt web UI (no Node build needed), and
starts the same Flask + SSE server the desktop web version uses. Downloaded
files go to `MMDL_DOWNLOADS` (default `~/storage/downloads`). Override with:

```bash
PORT=8080 MMDL_DOWNLOADS=~/storage/downloads bash termux/run-web.sh
```

To reach it from another device on your LAN, start it with `HOST=0.0.0.0`
(only on networks you trust — the server has no built-in authentication).

## Notes

- **ffmpeg** comes from Termux's own package, so conversions and audio
  extraction work natively (arm64).
- The **AI Assistant** works here too if you set an OpenRouter API key in the
  web UI's settings.
- Keeping the download alive: Termux may sleep in the background — acquire a
  wake lock (Termux notification → "Acquire wakelock") for long batches.

---

## 在 Android（Termux）上使用（中文速覽）

桌面 app 無法在 Android 執行，但底層引擎是純 Python（yt-dlp + ffmpeg），在
Termux 上可用。從 **F-Droid** 安裝 Termux（非 Play 商店版），建議先跑
`termux-setup-storage`。

```bash
pkg install -y git
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader

# A. 終端機 CLI
bash termux/run-cli.sh download "https://youtu.be/XXXX" -o ~/storage/downloads -f mp4
bash termux/run-cli.sh --help    # 或 python cli.py --help（加 --lang zh_tw 顯示中文訊息）

# B. 手機瀏覽器用 Web 版
bash termux/run-web.sh           # 開啟顯示的網址（如 http://127.0.0.1:8080）
```

檔案預設存到 `~/storage/downloads`。長時間批次下載時，於 Termux 通知列
「Acquire wakelock」避免系統休眠中斷。
