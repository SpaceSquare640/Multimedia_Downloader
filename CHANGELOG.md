# Changelog

**Language / 語言 / 语言:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

---

## English

### [4.1.0] — 2026-07-17

#### Added
- **Standalone web version** — the same UI now runs as a real, deployable web
  app via `web_app.py` (Flask + Server-Sent Events), driving the *same* engine
  (real yt-dlp / ffmpeg, not the browser mock). Build with
  `npm run build:frontend:web`, serve with `npm run web`
  (`HOST`/`PORT`/`MMDL_DOWNLOADS` configurable). It reuses the desktop's exact
  command/event protocol — only the transport changes (stdio → HTTP + SSE) —
  so the engine and AI code are untouched. Doubles as phone-browser access
  ahead of native mobile apps.

#### Fixed
- **AI Assistant runtime error** — the planner/summarizer OpenRouter model
  slugs had been delisted upstream, so the first planner call failed. Swapped
  to current free models (`meta-llama/llama-3.3-70b-instruct:free` planner,
  `meta-llama/llama-3.2-3b-instruct:free` summarizer); the AI Assistant works
  again on the packaged build. This resolves the V4.0 known limitation.

### [4.0.0] — 2026-07-10

#### Added
- **AI Assistant** — describe a batch task in plain language; a multi-model
  OpenRouter pipeline (planner → executor → deterministic safety guard →
  checker) drafts a plan that **only runs after explicit user confirmation**
  (nothing touches the filesystem before that click). Bring your own
  OpenRouter API key.
- **Native desktop app** — rebuilt around a [Tauri](https://tauri.app) shell
  (Rust) hosting a Svelte + TypeScript + Tailwind UI, replacing the tkinter
  desktop GUI. Windows installers (NSIS `.exe`, MSI `.msi`) ship with the
  Python engine and ffmpeg bundled — no separate Python or ffmpeg install
  required.
- **Modular multi-language architecture** — the former single-file `core.py`
  is now `engine/` (formats / options / downloader / converter / queue), with
  the frontend, Rust shell, and AI orchestration as separate layers connected
  by a documented stdio JSON-RPC protocol (`engine_sidecar.py`).
- **JSON-based i18n** — `locales/{en,zh_tw,zh_cn}.json` (165 keys) replace the
  hard-coded Python dict; adding a language no longer touches code.
- **Batch task queue** — mixed download + convert batches with per-item live
  status, used by both manual queuing and the AI assistant's confirmed plans.
- **Light / dark / system theme**, PWA-ready frontend, responsive layout
  (desktop tab bar / mobile bottom nav + AI bottom sheet).

#### Changed
- **Desktop-first scope** — V4.0 targets Windows / Linux / macOS desktop only;
  mobile app support is deferred to **V5.0**, and a real deployable web
  version (equivalent to V3.0's `web_app.py`) is deferred to **V4.1**. Opening
  the built frontend outside the desktop shell runs a mock preview only.
- Engine logic ported from V3.0 `core.py` with byte-identical yt-dlp option
  generation (verified by parity tests) — no behavior change to
  download/convert semantics, only structural.

#### Known limitations
- **AI Assistant currently errors at runtime on the packaged desktop build.**
  Since this is a low-usage feature, the fix is scheduled for **V4.1**
  (shipping together with the real web version) rather than blocking this
  release. All other features (video/audio download, format conversion,
  batch queue, stop/cancel, i18n) have been verified working with no errors
  on the packaged Windows installer.
- OpenRouter API key is stored in the browser's `localStorage`, not an OS
  keychain (flagged for future hardening).
- Linux / macOS installers are not yet built (require building on/for those
  platforms or CI); only the Windows build has been produced and verified.

### [3.0.0] — 2026-05-27 and earlier

See the V3.0 changelog for the full history up to the tkinter/Flask
generation of the app: the [v3.0.0 CHANGELOG](https://github.com/SpaceSquare640/Multimedia_Downloader/blob/v3.0.0/CHANGELOG.md).

---

## 繁體中文

### [4.1.0] — 2026-07-17

#### 新增
- **獨立網頁版** — 同一套 UI 現在可透過 `web_app.py`（Flask + Server-Sent
  Events）作為真正、可部署的網頁版執行，驅動**同一個引擎**（真 yt-dlp /
  ffmpeg，非瀏覽器模擬）。以 `npm run build:frontend:web` 建置、`npm run web`
  執行（`HOST`／`PORT`／`MMDL_DOWNLOADS` 可設定）。它重用桌面版完全相同的
  指令/事件協定——只換傳輸層（stdio → HTTP + SSE）——引擎與 AI 程式碼一行
  未改。也順帶讓手機瀏覽器可用，先於原生行動 App。

#### 修復
- **AI 助手運行時錯誤** — planner/summarizer 的 OpenRouter 模型 slug 被上游
  下架，導致第一個 planner 呼叫失敗。已換成現行免費模型（planner
  `meta-llama/llama-3.3-70b-instruct:free`、summarizer
  `meta-llama/llama-3.2-3b-instruct:free`）；AI 助手在打包版上恢復正常。此項
  解除了 V4.0 的已知限制。

### [4.0.0] — 2026-07-10

#### 新增
- **AI 助手** — 用自然語言描述批次任務；OpenRouter 多模型協作管線（規劃 →
  精煉 → 決定性安全防護閘 → 審查）產生計畫，**只有在你明確確認後才會執
  行**（按下確認前不會碰任何檔案系統）。使用者自帶 OpenRouter API Key。
- **原生桌面 app** — 以 [Tauri](https://tauri.app) 殼（Rust）承載 Svelte +
  TypeScript + Tailwind 前端重建，取代原本的 tkinter 桌面 GUI。Windows 安裝
  檔（NSIS `.exe`、MSI `.msi`）內建 Python 引擎與 ffmpeg——免另外安裝
  Python 或 ffmpeg。
- **模組化多語言架構** — 原本的單檔 `core.py` 拆為 `engine/`（formats /
  options / downloader / converter / queue），前端、Rust 殼、AI 編排各為獨
  立分層，以文件化的 stdio JSON-RPC 協定連接（`engine_sidecar.py`）。
- **JSON 化 i18n** — `locales/{en,zh_tw,zh_cn}.json`（165 keys）取代寫死的
  Python dict；新增語言不必改程式碼。
- **批次任務佇列** — 混合下載 + 轉換的批次作業，即時逐項狀態，供手動排隊
  與 AI 助手確認後的計畫共用。
- **亮/暗/系統主題**、PWA-ready 前端、響應式版面（桌面 tab bar／手機底部
  導航 + AI bottom sheet）。

#### 變更
- **桌面優先範圍** — V4.0 專注 Windows / Linux / macOS 三大桌面；行動端支
  援延後至 **V5.0**，真正可部署的網頁版（相當於 V3.0 `web_app.py`）延後至
  **V4.1**。在桌面殼之外開啟前端只是模擬預覽。
- 引擎邏輯移植自 V3.0 `core.py`，產生的 yt-dlp 參數逐位元組相同（已通過對
  等測試驗證）——下載/轉換行為無變化，只是架構重整。

#### 已知限制
- **AI 助手目前在打包桌面版上運行時會發生錯誤。** 因此功能使用頻率低，修
  復排入 **V4.1**（與真正的網頁版一併推出），不阻擋本次發布。其餘功能
  （影片/音訊下載、格式轉換、批次佇列、停止/取消、多語言）皆已在打包版
  Windows 安裝檔上驗證無誤。
- OpenRouter API Key 存於瀏覽器 `localStorage`，非 OS 金鑰庫（已記錄待未來
  強化）。
- Linux / macOS 安裝檔尚未建置（需在對應平台或 CI 上建置）；目前僅 Windows
  版已建置並驗證。

### [3.0.0] — 2026-05-27 及更早

tkinter/Flask 世代的完整變更歷程見 V3.0 changelog：
the [v3.0.0 CHANGELOG](https://github.com/SpaceSquare640/Multimedia_Downloader/blob/v3.0.0/CHANGELOG.md)。

---

## 简体中文

### [4.1.0] — 2026-07-17

#### 新增
- **独立网页版** — 同一套 UI 现在可通过 `web_app.py`（Flask + Server-Sent
  Events）作为真正、可部署的网页版运行，驱动**同一个引擎**（真 yt-dlp /
  ffmpeg，非浏览器模拟）。以 `npm run build:frontend:web` 构建、`npm run web`
  运行（`HOST`／`PORT`／`MMDL_DOWNLOADS` 可配置）。它复用桌面版完全相同的
  指令/事件协议——只换传输层（stdio → HTTP + SSE）——引擎与 AI 代码一行未
  改。也顺带让手机浏览器可用，先于原生移动 App。

#### 修复
- **AI 助手运行时错误** — planner/summarizer 的 OpenRouter 模型 slug 被上游
  下架，导致第一个 planner 调用失败。已换成现行免费模型（planner
  `meta-llama/llama-3.3-70b-instruct:free`、summarizer
  `meta-llama/llama-3.2-3b-instruct:free`）；AI 助手在打包版上恢复正常。此项
  解除了 V4.0 的已知限制。

### [4.0.0] — 2026-07-10

#### 新增
- **AI 助手** — 用自然语言描述批次任务；OpenRouter 多模型协作管线（规划 →
  细化 → 确定性安全防护闸 → 审查）生成计划，**只有在你明确确认后才会执
  行**（按下确认前不会触碰任何文件系统）。用户自带 OpenRouter API Key。
- **原生桌面 app** — 以 [Tauri](https://tauri.app) 壳（Rust）承载 Svelte +
  TypeScript + Tailwind 前端重建，取代原本的 tkinter 桌面 GUI。Windows 安装
  包（NSIS `.exe`、MSI `.msi`）内置 Python 引擎与 ffmpeg——免另外安装
  Python 或 ffmpeg。
- **模块化多语言架构** — 原本的单文件 `core.py` 拆为 `engine/`（formats /
  options / downloader / converter / queue），前端、Rust 壳、AI 编排各为独
  立分层，以文档化的 stdio JSON-RPC 协议连接（`engine_sidecar.py`）。
- **JSON 化 i18n** — `locales/{en,zh_tw,zh_cn}.json`（165 keys）取代硬编码
  的 Python dict；新增语言无需改动代码。
- **批次任务队列** — 混合下载 + 转换的批次作业，实时逐项状态，供手动排队
  与 AI 助手确认后的计划共用。
- **浅色/深色/跟随系统主题**、PWA-ready 前端、响应式布局（桌面 tab
  bar／手机底部导航 + AI bottom sheet）。

#### 变更
- **桌面优先范围** — V4.0 专注 Windows / Linux / macOS 三大桌面；移动端支
  持延后至 **V5.0**，真正可部署的网页版（相当于 V3.0 `web_app.py`）延后至
  **V4.1**。在桌面壳之外打开前端只是模拟预览。
- 引擎逻辑移植自 V3.0 `core.py`，生成的 yt-dlp 参数逐字节相同（已通过对等
  测试验证）——下载/转换行为无变化，只是架构重整。

#### 已知限制
- **AI 助手目前在打包桌面版上运行时会发生错误。** 因该功能使用频率低，修
  复排入 **V4.1**（与真正的网页版一并推出），不阻挡本次发布。其余功能
  （视频/音频下载、格式转换、批次队列、停止/取消、多语言）均已在打包版
  Windows 安装包上验证无误。
- OpenRouter API Key 存于浏览器 `localStorage`，非 OS 密钥库（已记录待未来
  强化）。
- Linux / macOS 安装包尚未构建（需在对应平台或 CI 上构建）；目前仅 Windows
  版已构建并验证。

### [3.0.0] — 2026-05-27 及更早

tkinter/Flask 世代的完整变更历程见 V3.0 changelog：
the [v3.0.0 CHANGELOG](https://github.com/SpaceSquare640/Multimedia_Downloader/blob/v3.0.0/CHANGELOG.md)。
