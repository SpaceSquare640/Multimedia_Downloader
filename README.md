# Multimedia Downloader — V4.0

A cross-platform multimedia downloader & format converter built on top of
[yt-dlp](https://github.com/yt-dlp/yt-dlp) and `ffmpeg`, with an AI assistant
for batch automation. Ships as a native desktop app (Windows / Linux / macOS)
built with [Tauri](https://tauri.app).

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

> [!NOTE]
> V4.0 is a desktop app only. A real, network-deployable web version (like
> V3.0's `web_app.py`) is planned for **V4.1**; native mobile apps are planned
> for **V5.0**.

### Install (end users)

1. Download the installer for your platform from `Packaged/` (Windows: `.exe`
   or `.msi`).
2. Run it and follow the prompts.
3. Launch **Multimedia Downloader** from the Start Menu / Applications.

No separate Python or ffmpeg install is required — both are bundled inside
the app.

### Using the AI Assistant

> [!WARNING]
> The AI Assistant currently errors at runtime in the 4.0.0 build. A fix is
> scheduled for **v4.1** (shipping alongside the real web version). All other
> features (video/audio download, format conversion, batch queue) are
> unaffected and verified working.

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
| Windows 10/11, Linux, or macOS | Desktop app; Windows build verified, Linux/macOS packaging pending CI. |
| WebView2 | Pre-installed on modern Windows; the installer will prompt if missing. |
| OpenRouter API key | **Optional** — only needed to use the AI Assistant. Get one free at [openrouter.ai](https://openrouter.ai/keys). |

### Building from source (developers)

```bash
git clone -b Version4.0 https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
npm install                 # installs the Tauri CLI at the project root
npm run tauri dev           # compile + run in dev mode (needs Python 3.8+, Rust, Node)
npm run package             # build installers -> Packaged/Version4.0_Packaged
```

Run the Python test suite: `python -m unittest discover -s tests` (63 tests).

### Project layout

```
Version4.0/
├── src-tauri/    Tauri shell (Rust): window, sidecar management
├── frontend/     Web UI (Svelte + Vite + TS + Tailwind)
├── engine/       Python engine: Downloader / Converter (yt-dlp + ffmpeg)
├── engine_sidecar.py   stdio IPC entrypoint spawned by the Rust shell
├── ai/           OpenRouter client + multi-model planning pipeline
├── locales/      en.json / zh_tw.json / zh_cn.json
├── packaging/    PyInstaller spec + build script
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

> [!NOTE]
> V4.0 目前僅為桌面 app。真正可部署、能用的網頁版（如 V3.0 的
> `web_app.py`）規劃於 **V4.1**；原生行動 App 規劃於 **V5.0**。

### 安裝（一般使用者）

1. 從 `Packaged/` 下載對應平台的安裝檔（Windows：`.exe` 或 `.msi`）。
2. 執行並依提示安裝。
3. 從開始選單／應用程式啟動 **Multimedia Downloader**。

不需要另外安裝 Python 或 ffmpeg——兩者皆已內建於 app 中。

### 使用 AI 助手

> [!WARNING]
> 4.0.0 版本中 AI 助手目前運行時會發生錯誤，修復已排入 **v4.1**（與真正的
> 網頁版一併推出）。其餘功能（影片/音訊下載、格式轉換、批次佇列）不受影
> 響，已驗證正常。

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
| Windows 10/11、Linux 或 macOS | 桌面 app；Windows 版已驗證，Linux/macOS 打包待對應 CI。 |
| WebView2 | 現代 Windows 已預裝；安裝程式會在缺少時提示安裝。 |
| OpenRouter API Key | **選用**——僅使用 AI 助手時需要。至 [openrouter.ai](https://openrouter.ai/keys) 免費取得。 |

### 從原始碼建置（開發者）

```bash
git clone -b Version4.0 https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
npm install                 # 於專案根目錄安裝 Tauri CLI
npm run tauri dev           # 編譯並以開發模式執行（需 Python 3.8+、Rust、Node）
npm run package             # 建置安裝檔 → Packaged/Version4.0_Packaged
```

執行 Python 測試套件：`python -m unittest discover -s tests`（63 項測試）。

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

> [!NOTE]
> V4.0 目前仅为桌面 app。真正可部署、能用的网页版（如 V3.0 的
> `web_app.py`）规划于 **V4.1**；原生移动端 App 规划于 **V5.0**。

### 安装（普通用户）

1. 从 `Packaged/` 下载对应平台的安装包（Windows：`.exe` 或 `.msi`）。
2. 运行并按提示安装。
3. 从开始菜单／应用程序启动 **Multimedia Downloader**。

不需要另外安装 Python 或 ffmpeg——两者均已内置于 app 中。

### 使用 AI 助手

> [!WARNING]
> 4.0.0 版本中 AI 助手目前运行时会发生错误，修复已排入 **v4.1**（与真正的
> 网页版一并推出）。其余功能（视频/音频下载、格式转换、批次队列）不受影
> 响，已验证正常。

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
| Windows 10/11、Linux 或 macOS | 桌面 app；Windows 版已验证，Linux/macOS 打包待对应 CI。 |
| WebView2 | 现代 Windows 已预装；安装程序会在缺少时提示安装。 |
| OpenRouter API Key | **可选**——仅使用 AI 助手时需要。到 [openrouter.ai](https://openrouter.ai/keys) 免费获取。 |

### 从源代码构建（开发者）

```bash
git clone -b Version4.0 https://github.com/SpaceSquare640/Multimedia_Downloader.git
cd Multimedia_Downloader
npm install                 # 在项目根目录安装 Tauri CLI
npm run tauri dev           # 编译并以开发模式运行（需 Python 3.8+、Rust、Node）
npm run package             # 构建安装包 → Packaged/Version4.0_Packaged
```

运行 Python 测试套件：`python -m unittest discover -s tests`（63 项测试）。

### Cookie 提示

部分平台（抖音、私人 TikTok、私人 Instagram 等）必须带上登录 Cookie 才能下载：

1. **直接读取浏览器（最方便）** — 在下载标签页选择你已登录的浏览器，
   yt-dlp 会自动读取其 Cookie。
2. **手动导入文件** — 用扩展（Chrome/Edge/Brave 安装
   *Get cookies.txt LOCALLY*；Firefox 安装 *cookies.txt*）导出
   `cookies.txt`。

### 声明

本软件仅供个人合法使用。请遵守各平台的服务条款与内容版权。
