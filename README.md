# Multimedia Downloader

A cross-platform multimedia downloader & format converter built on top of
[yt-dlp](https://github.com/yt-dlp/yt-dlp) and `ffmpeg`. Ships with both a
native desktop GUI (tkinter) and a browser-based web app (Flask).

**Language / 語言 / 语言:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

---

## English

### Highlights

- **Two interfaces, one engine** — desktop GUI (`Multimedia_Downloader.py`) and
  web app (`web_app.py`) share the same `core.Downloader` / `core.Converter`.
- **Online or local** — run the web app locally, or deploy it to any WSGI host
  (Render, Railway, Fly.io, your own VPS).
- **Tri-language UI** — English (default), Traditional Chinese, Simplified
  Chinese; switchable at runtime in both interfaces.
- **500+ sites** — YouTube, Facebook, Instagram, TikTok, BiliBili, Twitter,
  SoundCloud, Twitch, Vimeo, and every other site yt-dlp supports.
- **Audio extraction** — convert to MP3, FLAC, AAC, WAV, OGG, M4A, Opus, WMA.
- **Format conversion** — transcode any input to any output via ffmpeg.
- **Cookie support** — read from an installed browser, or supply a
  `cookies.txt` for Douyin / Instagram / login-gated platforms.
- **Optional session logging** — auto-save the download log as `.txt`.

### Requirements

| Component        | Notes                                                          |
| ---------------- | -------------------------------------------------------------- |
| Python 3.8+      | Required by both interfaces.                                   |
| `yt-dlp`         | Auto-installed by the desktop GUI on first launch.             |
| `Pillow`, `requests` | Auto-installed by the desktop GUI on first launch.         |
| `Flask`          | Required for the web app (`pip install -r requirements.txt`).  |
| ffmpeg           | **Optional but recommended** — required for audio extraction and conversion. Install from [ffmpeg.org](https://ffmpeg.org) and add to `PATH`. |
| tkinter          | Standard library on Windows/macOS. On Debian/Ubuntu: `sudo apt install python3-tk`. |

### Install

```bash
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
pip install -r requirements.txt
```

### Usage — Desktop GUI

```bash
python Multimedia_Downloader.py
```

1. Paste one URL per line in the URL box.
2. Pick video / audio mode, format, and quality.
3. Choose a save folder.
4. Click **Start Download**.
5. Switch language any time from the dropdown in the top-right corner.

### Usage — Web App

Run locally:

```bash
python web_app.py
# → http://127.0.0.1:5000
```

Deploy to a server (any WSGI host):

```bash
HOST=0.0.0.0 PORT=8000 python web_app.py
# or with gunicorn:
gunicorn -w 1 -b 0.0.0.0:8000 web_app:app
```

Finished files are placed in the `downloads/` directory next to `web_app.py`
and served back to clients via `/files/<name>`.

### Project layout

```
Multimedia_Downloader/
├── Multimedia_Downloader.py    Desktop GUI (tkinter)
├── web_app.py                  Flask web server
├── core.py                     yt-dlp + ffmpeg engine, UI-agnostic
├── i18n.py                     Translation tables (en / zh_tw / zh_cn)
├── templates/
│   └── index.html              Web UI
├── static/
│   ├── styles.css
│   └── script.js
├── requirements.txt
├── README.md
├── CHANGELOG.md
└── .gitignore
```

### Cookie tips

Some platforms (Douyin, private TikTok, private Instagram) refuse to serve
media without an authenticated cookie. Two options:

1. **Browser-direct (easiest)** — select the browser you are logged into from
   the dropdown. yt-dlp will read its cookies for you.
2. **Manual file** — export `cookies.txt` with a browser extension
   (e.g. *Get cookies.txt LOCALLY* for Chrome/Edge/Brave, *cookies.txt* for
   Firefox), then point the GUI at it.

### Disclaimer

This software is for personal, lawful use only. Respect each platform's terms
of service and the copyright of content owners.

---

## 繁體中文

### 功能特色

- **雙介面、同引擎** — 桌面版 (`Multimedia_Downloader.py`) 與網頁版
  (`web_app.py`) 共用 `core.Downloader` / `core.Converter`。
- **線上或本機** — 網頁版可在本機執行，或部署至任意 WSGI 主機（Render、
  Railway、Fly.io、自架 VPS 等）。
- **三語介面** — 英文（預設）、繁體中文、簡體中文，兩種介面皆可即時切換。
- **500+ 平台** — YouTube、Facebook、Instagram、TikTok、BiliBili、Twitter、
  SoundCloud、Twitch、Vimeo 等。
- **音訊擷取** — 轉換為 MP3、FLAC、AAC、WAV、OGG、M4A、Opus、WMA。
- **格式轉換** — 透過 ffmpeg 任意轉碼。
- **Cookie 支援** — 直接讀取已登入的瀏覽器，或匯入 `cookies.txt` 處理抖音、
  Instagram 等需登入平台。
- **可選日誌儲存** — 自動將下載日誌存為 `.txt`。

### 安裝需求

| 組件 | 說明 |
| --- | --- |
| Python 3.8+ | 兩種介面均需要。 |
| `yt-dlp`、`Pillow`、`requests` | 桌面版首次啟動會自動安裝。 |
| `Flask` | 網頁版需要：`pip install -r requirements.txt`。 |
| ffmpeg | **選用但建議** — 音訊擷取與格式轉換需要。至 [ffmpeg.org](https://ffmpeg.org) 下載並加入 `PATH`。 |
| tkinter | Windows / macOS 隨附。Debian / Ubuntu：`sudo apt install python3-tk`。 |

### 安裝

```bash
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
pip install -r requirements.txt
```

### 使用方式 — 桌面版

```bash
python Multimedia_Downloader.py
```

1. 在 URL 框內貼上連結（每行一個）。
2. 選擇影片／音訊模式、格式、畫質。
3. 選擇存放資料夾。
4. 點擊「開始下載」。
5. 可隨時從右上角下拉選單切換語言。

### 使用方式 — 網頁版

本機執行：

```bash
python web_app.py
# → http://127.0.0.1:5000
```

部署到伺服器（任意 WSGI 主機）：

```bash
HOST=0.0.0.0 PORT=8000 python web_app.py
# 或使用 gunicorn：
gunicorn -w 1 -b 0.0.0.0:8000 web_app:app
```

完成的檔案會放在 `web_app.py` 同層的 `downloads/` 資料夾，並透過
`/files/<檔名>` 提供下載。

### Cookie 提示

部分平台（抖音、私人 TikTok、私人 Instagram 等）必須帶上登入 Cookie 才能下載：

1. **直接讀取瀏覽器（最方便）** — 從下拉選單選擇你已登入的瀏覽器，
   yt-dlp 會自動讀取其 Cookie。
2. **手動匯入檔案** — 用擴充功能（Chrome/Edge/Brave 安裝
   *Get cookies.txt LOCALLY*；Firefox 安裝 *cookies.txt*）匯出
   `cookies.txt`，再於介面中指定。

### 聲明

本軟體僅供個人合法使用。請遵守各平台的服務條款與內容版權。

---

## 简体中文

### 功能特色

- **双界面、同引擎** — 桌面版 (`Multimedia_Downloader.py`) 与网页版
  (`web_app.py`) 共用 `core.Downloader` / `core.Converter`。
- **在线或本机** — 网页版可在本机运行，或部署到任意 WSGI 主机（Render、
  Railway、Fly.io、自建 VPS 等）。
- **三语界面** — 英文（默认）、繁体中文、简体中文，两种界面均可即时切换。
- **500+ 平台** — YouTube、Facebook、Instagram、TikTok、BiliBili、Twitter、
  SoundCloud、Twitch、Vimeo 等。
- **音频提取** — 转换为 MP3、FLAC、AAC、WAV、OGG、M4A、Opus、WMA。
- **格式转换** — 通过 ffmpeg 任意转码。
- **Cookie 支持** — 直接读取已登录的浏览器，或导入 `cookies.txt` 处理抖音、
  Instagram 等需登录平台。
- **可选日志保存** — 自动将下载日志保存为 `.txt`。

### 安装需求

| 组件 | 说明 |
| --- | --- |
| Python 3.8+ | 两种界面均需要。 |
| `yt-dlp`、`Pillow`、`requests` | 桌面版首次启动会自动安装。 |
| `Flask` | 网页版需要：`pip install -r requirements.txt`。 |
| ffmpeg | **可选但推荐** — 音频提取与格式转换需要。从 [ffmpeg.org](https://ffmpeg.org) 下载并加入 `PATH`。 |
| tkinter | Windows / macOS 自带。Debian / Ubuntu：`sudo apt install python3-tk`。 |

### 安装

```bash
git clone https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
pip install -r requirements.txt
```

### 使用方式 — 桌面版

```bash
python Multimedia_Downloader.py
```

1. 在 URL 框内粘贴链接（每行一个）。
2. 选择视频／音频模式、格式、画质。
3. 选择存放文件夹。
4. 点击「开始下载」。
5. 可随时从右上角下拉菜单切换语言。

### 使用方式 — 网页版

本机运行：

```bash
python web_app.py
# → http://127.0.0.1:5000
```

部署到服务器（任意 WSGI 主机）：

```bash
HOST=0.0.0.0 PORT=8000 python web_app.py
# 或使用 gunicorn：
gunicorn -w 1 -b 0.0.0.0:8000 web_app:app
```

完成的文件会放在 `web_app.py` 同层的 `downloads/` 文件夹，并通过
`/files/<文件名>` 提供下载。

### Cookie 提示

部分平台（抖音、私人 TikTok、私人 Instagram 等）必须带上登录 Cookie 才能下载：

1. **直接读取浏览器（最方便）** — 从下拉菜单选择你已登录的浏览器，
   yt-dlp 会自动读取其 Cookie。
2. **手动导入文件** — 用扩展（Chrome/Edge/Brave 安装
   *Get cookies.txt LOCALLY*；Firefox 安装 *cookies.txt*）导出
   `cookies.txt`，再在界面中指定。

### 声明

本软件仅供个人合法使用。请遵守各平台的服务条款与内容版权。
