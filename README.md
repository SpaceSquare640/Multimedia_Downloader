# Multimedia Downloader — V4.2.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/SpaceSquare640/Multimedia_Downloader?sort=semver)](https://github.com/SpaceSquare640/Multimedia_Downloader/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/SpaceSquare640/Multimedia_Downloader/total)](https://github.com/SpaceSquare640/Multimedia_Downloader/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Web-blue)](#run-as-a-web-app-v41)
[![Built with](https://img.shields.io/badge/built%20with-Tauri%20·%20Svelte%20·%20Python-6E56CF)](#project-layout)

A cross-platform multimedia downloader & format converter built on top of
[yt-dlp](https://github.com/yt-dlp/yt-dlp) and `ffmpeg`, with an AI assistant
for batch automation. Ships as a native desktop app (Windows / Linux / macOS)
built with [Tauri](https://tauri.app), and as a deployable web app.

**Language / 語言 / 语言:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

---

## English

### Highlights

- **AI Assistant** — describe what you want in plain language ("convert every
  .mkv in this folder to mp4"); the assistant drafts a batch plan and **only
  runs it after you confirm** — nothing executes without your approval.
- **500+ sites** — YouTube, Facebook, Instagram, TikTok, BiliBili, Twitter,
  SoundCloud, Twitch, Vimeo, and every other site yt-dlp supports.
- **Audio extraction** — convert to MP3, FLAC, AAC, WAV, OGG, M4A, Opus, WMA.
- **Format conversion** — transcode any input to any output via ffmpeg
  (bundled — no separate ffmpeg install needed).
- **Tri-language UI** — English (default), Traditional Chinese, Simplified
  Chinese; switchable at runtime.
- **Cookie support** — read from an installed browser, or supply a
  `cookies.txt` for Douyin / Instagram / login-gated platforms.
- **Batch queue** — download or convert many items in one go, with live
  per-item progress and a run log.
- **Built-in User Manual** — a quick reference panel right in the app (header
  book icon), available in all three languages.

> [!NOTE]
> Primarily a desktop app; **V4.1** adds a real, network-deployable web version
> (see [Run as a web app](#run-as-a-web-app-v41) below). Native mobile apps are
> planned for **V5.0**.

### Install (end users)

1. Download the installer for your platform from the [Releases page](https://github.com/SpaceSquare640/Multimedia_Downloader/releases/latest) (Windows: `.exe`
   or `.msi`).
2. Run it and follow the prompts.
3. Launch **Multimedia Downloader** from the Start Menu / Applications.

No separate Python or ffmpeg install is required — both are bundled inside
the app.

### Using the AI Assistant

> [!NOTE]
> The AI Assistant runtime error in the 4.0.0 build is **fixed in v4.1** (the
> planner/summarizer OpenRouter models had been delisted upstream and were
> swapped for current free models).

1. Click the **✨ AI Assistant** button (or press `Ctrl/Cmd+K`).
2. First time only: open **Settings** and paste your own
   [OpenRouter](https://openrouter.ai/keys) API key (stored locally on your
   device only — never bundled, never sent anywhere but OpenRouter).
3. Describe your task, e.g. *"Download
   https://youtube.com/watch?v=... as mp4"* or *"Convert D:\videos\a.mov and
   b.avi to mp4"*.
4. Review the generated plan — **nothing runs yet**.
5. Click **Confirm** to execute, or **Cancel** / **Regenerate**.

### Requirements

| Component | Notes |
| --- | --- |
| Windows 10/11, Linux, or macOS | Desktop app; all three platforms built and published automatically by CI. |
| WebView2 | Pre-installed on modern Windows; the installer will prompt if missing. |
| OpenRouter API key | **Optional** — only needed to use the AI Assistant. Get one free at [openrouter.ai](https://openrouter.ai/keys). |

### Building from source (developers)

```bash
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
npm install                 # installs the Tauri CLI at the project root
npm run tauri dev           # compile + run in dev mode (needs Python 3.8+, Rust, Node)
npm run tauri build         # build an installer locally, if you want one without waiting for CI
```

Official installers for every push tag are built and published automatically
by GitHub Actions (see `.github/workflows/release.yml`) — you don't need to
build locally to cut a release, just push a `vX.Y.Z` tag.

Run the Python test suite: `python -m unittest discover -s tests` (63 tests).

### Run as a web app (V4.1)

The same UI can run as a standalone, deployable web app — no desktop shell —
with a real Flask + SSE backend that drives the *same* engine (real yt-dlp /
ffmpeg, not the browser mock):

```bash
cd Multimedia_Downloader
pip install -r requirements-web.txt   # yt-dlp + Flask (ffmpeg on PATH)
npm run build:frontend:web            # build the frontend in web mode
npm run web                           # serve on http://127.0.0.1:5000
# LAN / server:
HOST=0.0.0.0 PORT=8000 python web_app.py
```

Because it's a browser app, downloaded/converted files land in a **server-side**
folder (`MMDL_DOWNLOADS`, default `./downloads`) retrievable at `/files/<name>`
— leave the Save-Location field blank to use it. It's a single-user model (one
operation at a time, like V3.0's `web_app.py`); for production put it behind a
streaming-friendly WSGI worker, e.g. `gunicorn -k gthread -w 1 --threads 8
web_app:app`, and add your own auth if exposing it beyond localhost.

### Run on Android (Termux)

The desktop app can't run on Android, but the Python engine can — via
[Termux](https://termux.dev). Use it from the terminal (CLI) or as the web UI
in your phone's browser:

```bash
pkg install -y git && git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
bash termux/run-cli.sh download "https://youtu.be/XXXX" -o ~/storage/downloads -f mp4   # CLI
bash termux/run-web.sh                                                                  # web UI
```

Full walkthrough: [termux/README.md](termux/README.md). The CLI ([`cli.py`](cli.py))
also runs on any desktop/server with Python + ffmpeg.

### Project layout

```
Source_Code/
├── src-tauri/    Tauri shell (Rust): window, sidecar management
├── frontend/     Web UI (Svelte + Vite + TS + Tailwind)
├── engine/       Python engine: Downloader / Converter (yt-dlp + ffmpeg)
├── engine_sidecar.py   stdio IPC entrypoint spawned by the Rust shell
├── web_app.py    Flask + SSE backend for the standalone web app (V4.1)
├── cli.py        terminal CLI over the engine (great for Termux / headless)
├── termux/       Android (Termux) launchers + guide
├── ai/           OpenRouter client + multi-model planning pipeline
├── locales/      en.json / zh_tw.json / zh_cn.json
├── packaging/    PyInstaller spec (used by CI to build the sidecar)
└── tests/        Unit tests
```

### Cookie tips

Some platforms (Douyin, private TikTok, private Instagram) refuse to serve
media without an authenticated cookie:

1. **Browser-direct (easiest)** — select the browser you are logged into in
   the download tab. yt-dlp reads its cookies for you.
2. **Manual file** — export `cookies.txt` with a browser extension (e.g.
   *Get cookies.txt LOCALLY* for Chrome/Edge/Brave, *cookies.txt* for
   Firefox).

### Disclaimer

This software is for personal, lawful use only. Respect each platform's terms
of service and the copyright of content owners.

---

## 繁體中文

### 功能特色

- **AI 助手** — 用自然語言描述需求（例如「把這個資料夾內所有 .mkv 轉成
  mp4」），助手會產生批次計畫，**執行前一定先給你確認**——沒有你的批准，
  不會有任何動作發生。
- **500+ 平台** — YouTube、Facebook、Instagram、TikTok、BiliBili、Twitter、
  SoundCloud、Twitch、Vimeo 等，凡 yt-dlp 支援皆可。
- **音訊擷取** — 轉換為 MP3、FLAC、AAC、WAV、OGG、M4A、Opus、WMA。
- **格式轉換** — 透過 ffmpeg 任意轉碼（已內建，免另外安裝 ffmpeg）。
- **三語介面** — 英文（預設）、繁體中文、簡體中文，可即時切換。
- **Cookie 支援** — 直接讀取已登入瀏覽器，或匯入 `cookies.txt` 處理抖音、
  Instagram 等需登入平台。
- **批次佇列** — 一次下載或轉換多個項目，即時逐項進度與運行日誌。
- **App 內建使用手冊** — 頁首書本圖示點開即可查看，支援三語。

> [!NOTE]
> 以桌面 app 為主；**V4.1** 新增真正可部署的網頁版（見下方「以網頁版執
> 行」）。原生行動 App 規劃於 **V5.0**。

### 安裝（一般使用者）

1. 從 [Releases 頁面](https://github.com/SpaceSquare640/Multimedia_Downloader/releases/latest) 下載對應平台的安裝檔（Windows：`.exe` 或 `.msi`）。
2. 執行並依提示安裝。
3. 從開始選單／應用程式啟動 **Multimedia Downloader**。

不需要另外安裝 Python 或 ffmpeg——兩者皆已內建於 app 中。

### 使用 AI 助手

> [!NOTE]
> 4.0.0 版本中 AI 助手的運行時錯誤已在 **v4.1 修復**（planner/summarizer 的
> OpenRouter 模型遭上游下架，已換成現行免費模型）。

1. 點擊 **✨ AI 助手** 按鈕（或按 `Ctrl/Cmd+K`）。
2. 第一次使用需到**設定**貼上你自己的
   [OpenRouter](https://openrouter.ai/keys) API Key（僅存於本機裝置，不隨
   app 打包、除了 OpenRouter 外不傳送給任何人）。
3. 描述你的需求，例如「把 https://youtube.com/watch?v=... 下載成 mp4」或
   「把 D:\videos\a.mov 和 b.avi 轉成 mp4」。
4. 檢查產生的計畫——**此時尚未執行任何動作**。
5. 點擊**確認**執行，或**取消**／**重新生成**。

### 安裝需求

| 組件 | 說明 |
| --- | --- |
| Windows 10/11、Linux 或 macOS | 桌面 app；三平台皆由 CI 自動建置並發布。 |
| WebView2 | 現代 Windows 已預裝；安裝程式會在缺少時提示安裝。 |
| OpenRouter API Key | **選用**——僅使用 AI 助手時需要。至 [openrouter.ai](https://openrouter.ai/keys) 免費取得。 |

### 從原始碼建置（開發者）

```bash
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
npm install                 # 於專案根目錄安裝 Tauri CLI
npm run tauri dev           # 編譯並以開發模式執行（需 Python 3.8+、Rust、Node）
npm run tauri build         # 想在本機直接建置安裝檔（不等 CI）時使用
```

每次推送 `vX.Y.Z` tag，GitHub Actions 會自動建置並發布各平台正式安裝檔（見
`.github/workflows/release.yml`）——正式發布不需要本機建置，推 tag 即可。

執行 Python 測試套件：`python -m unittest discover -s tests`（63 項測試）。

### 以網頁版執行（V4.1）

同一套 UI 可作為獨立、可部署的**網頁版**執行（不需桌面外殼），後端是真正的
Flask + SSE，驅動**同一個引擎**（真 yt-dlp / ffmpeg，非瀏覽器模擬）：

```bash
cd Multimedia_Downloader
pip install -r requirements-web.txt   # yt-dlp + Flask（ffmpeg 需在 PATH）
npm run build:frontend:web            # 以 web 模式建置前端
npm run web                           # 服務於 http://127.0.0.1:5000
# 區網 / 伺服器：
HOST=0.0.0.0 PORT=8000 python web_app.py
```

因為是瀏覽器 app，下載/轉換的檔案會落在**伺服器端**資料夾（`MMDL_DOWNLOADS`，
預設 `./downloads`），可經 `/files/<檔名>` 取回——存放位置欄位留空即用它。採單一
使用者模型（一次一個操作，同 V3.0 的 `web_app.py`）；正式部署請置於支援串流的
WSGI worker 後（例如 `gunicorn -k gthread -w 1 --threads 8 web_app:app`），對外開放時請自行加上驗證。

### 在 Android 上執行（Termux）

桌面版無法在 Android 執行，但 Python 引擎可以——透過 [Termux](https://termux.dev)。
可用終端機（CLI）或手機瀏覽器（Web 版）：

```bash
pkg install -y git && git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
bash termux/run-cli.sh download "https://youtu.be/XXXX" -o ~/storage/downloads -f mp4   # CLI
bash termux/run-web.sh                                                                  # Web 版
```

完整說明見 [termux/README.md](termux/README.md)。CLI（[`cli.py`](cli.py)）在任何有
Python + ffmpeg 的桌面/伺服器也能用。

### Cookie 提示

部分平台（抖音、私人 TikTok、私人 Instagram 等）必須帶上登入 Cookie 才能下載：

1. **直接讀取瀏覽器（最方便）** — 在下載分頁選擇你已登入的瀏覽器，yt-dlp
   會自動讀取其 Cookie。
2. **手動匯入檔案** — 用擴充功能（Chrome/Edge/Brave 安裝
   *Get cookies.txt LOCALLY*；Firefox 安裝 *cookies.txt*）匯出
   `cookies.txt`。

### 聲明

本軟體僅供個人合法使用。請遵守各平台的服務條款與內容版權。

---

## 简体中文

### 功能特色

- **AI 助手** — 用自然语言描述需求（例如「把这个文件夹内所有 .mkv 转成
  mp4」），助手会生成批次计划，**执行前一定先请你确认**——没有你的批准，
  不会有任何动作发生。
- **500+ 平台** — YouTube、Facebook、Instagram、TikTok、BiliBili、Twitter、
  SoundCloud、Twitch、Vimeo 等，凡 yt-dlp 支持皆可。
- **音频提取** — 转换为 MP3、FLAC、AAC、WAV、OGG、M4A、Opus、WMA。
- **格式转换** — 通过 ffmpeg 任意转码（已内置，免另外安装 ffmpeg）。
- **三语界面** — 英文（默认）、繁体中文、简体中文，可即时切换。
- **Cookie 支持** — 直接读取已登录浏览器，或导入 `cookies.txt` 处理抖音、
  Instagram 等需登录平台。
- **批次队列** — 一次下载或转换多个项目，实时逐项进度与运行日志。
- **App 内置使用手册** — 页首书本图标点开即可查看，支持三语。

> [!NOTE]
> 以桌面 app 为主；**V4.1** 新增真正可部署的网页版（见下方「以网页版运
> 行」）。原生移动端 App 规划于 **V5.0**。

### 安装（普通用户）

1. 从 [Releases 页面](https://github.com/SpaceSquare640/Multimedia_Downloader/releases/latest) 下载对应平台的安装包（Windows：`.exe` 或 `.msi`）。
2. 运行并按提示安装。
3. 从开始菜单／应用程序启动 **Multimedia Downloader**。

不需要另外安装 Python 或 ffmpeg——两者均已内置于 app 中。

### 使用 AI 助手

> [!NOTE]
> 4.0.0 版本中 AI 助手的运行时错误已在 **v4.1 修复**（planner/summarizer 的
> OpenRouter 模型被上游下架，已换成现行免费模型）。

1. 点击 **✨ AI 助手** 按钮（或按 `Ctrl/Cmd+K`）。
2. 首次使用需到**设置**粘贴你自己的
   [OpenRouter](https://openrouter.ai/keys) API Key（仅保存于本机设备，不
   随 app 打包、除 OpenRouter 外不发送给任何人）。
3. 描述你的需求，例如「把 https://youtube.com/watch?v=... 下载成 mp4」或
   「把 D:\videos\a.mov 和 b.avi 转成 mp4」。
4. 检查生成的计划——**此时尚未执行任何动作**。
5. 点击**确认**执行，或**取消**／**重新生成**。

### 安装需求

| 组件 | 说明 |
| --- | --- |
| Windows 10/11、Linux 或 macOS | 桌面 app；三平台均由 CI 自动构建并发布。 |
| WebView2 | 现代 Windows 已预装；安装程序会在缺少时提示安装。 |
| OpenRouter API Key | **可选**——仅使用 AI 助手时需要。到 [openrouter.ai](https://openrouter.ai/keys) 免费获取。 |

### 从源代码构建（开发者）

```bash
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
npm install                 # 在项目根目录安装 Tauri CLI
npm run tauri dev           # 编译并以开发模式运行（需 Python 3.8+、Rust、Node）
npm run tauri build         # 想在本机直接构建安装包（不等 CI）时使用
```

每次推送 `vX.Y.Z` tag，GitHub Actions 会自动构建并发布各平台正式安装包（见
`.github/workflows/release.yml`）——正式发布不需要本机构建，推 tag 即可。

运行 Python 测试套件：`python -m unittest discover -s tests`（63 项测试）。

### 以网页版运行（V4.1）

同一套 UI 可作为独立、可部署的**网页版**运行（不需桌面外壳），后端是真正的
Flask + SSE，驱动**同一个引擎**（真 yt-dlp / ffmpeg，非浏览器模拟）：

```bash
cd Multimedia_Downloader
pip install -r requirements-web.txt   # yt-dlp + Flask（ffmpeg 需在 PATH）
npm run build:frontend:web            # 以 web 模式构建前端
npm run web                           # 服务于 http://127.0.0.1:5000
# 局域网 / 服务器：
HOST=0.0.0.0 PORT=8000 python web_app.py
```

因为是浏览器 app，下载/转换的文件会落在**服务器端**文件夹（`MMDL_DOWNLOADS`，
默认 `./downloads`），可经 `/files/<文件名>` 取回——存放位置栏位留空即用它。采用单
用户模型（一次一个操作，同 V3.0 的 `web_app.py`）；正式部署请置于支持流式的 WSGI
worker 后（例如 `gunicorn -k gthread -w 1 --threads 8 web_app:app`），对外开放时请自行加上鉴权。

### 在 Android 上运行（Termux）

桌面版无法在 Android 运行，但 Python 引擎可以——通过 [Termux](https://termux.dev)。
可用终端（CLI）或手机浏览器（Web 版）：

```bash
pkg install -y git && git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
bash termux/run-cli.sh download "https://youtu.be/XXXX" -o ~/storage/downloads -f mp4   # CLI
bash termux/run-web.sh                                                                  # Web 版
```

完整说明见 [termux/README.md](termux/README.md)。CLI（[`cli.py`](cli.py)）在任何有
Python + ffmpeg 的桌面/服务器也能用。

### Cookie 提示

部分平台（抖音、私人 TikTok、私人 Instagram 等）必须带上登录 Cookie 才能下载：

1. **直接读取浏览器（最方便）** — 在下载标签页选择你已登录的浏览器，
   yt-dlp 会自动读取其 Cookie。
2. **手动导入文件** — 用扩展（Chrome/Edge/Brave 安装
   *Get cookies.txt LOCALLY*；Firefox 安装 *cookies.txt*）导出
   `cookies.txt`。

### 声明

本软件仅供个人合法使用。请遵守各平台的服务条款与内容版权。
