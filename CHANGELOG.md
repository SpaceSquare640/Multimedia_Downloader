# Changelog

**Language / 語言 / 语言:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

> Entries through v4.2.2 are tri-lingual. From the next release onward, new
> entries are written in English only (repo documentation is English-only
> going forward; the Wiki and the app's own UI remain tri-lingual).

---

## English

### [4.2.2] — 2026-07-23

#### Added
- **Confirm-before-clear for the Run Log** — clicking "Clear" now asks for
  confirmation first instead of wiping the log instantly with no way back
  (export it first if you need to keep a copy).
- A language icon next to the language selector in the header.

#### Changed
- CI now runs the full test suite (63 Python unit tests, `svelte-check`,
  `cargo check`/`clippy`) on every push to `main`, catching regressions before
  they can reach a tagged release. No effect on the app itself.

### [4.2.1] — 2026-07-23

#### Fixed
- **Language dropdown showing raw codes instead of names** (`en` / `zh_tw` /
  `zh_cn` instead of "English" / "繁體中文" / "简体中文") — reported in
  [#4](https://github.com/SpaceSquare640/Multimedia_Downloader/issues/4). The
  display names were being fetched over an unnecessary round-trip to the
  engine sidecar; if that round-trip ever hiccupped, the dropdown silently
  fell back to raw codes with no visible error. Fixed by reading the names
  directly from the locale files bundled at build time — zero backend
  dependency, so this can no longer happen.

#### Changed
- Removed the local-only `packaging/build-desktop.ps1` script and the
  `package` npm script that called it — CI's release pipeline has its own
  equivalent steps and never used this file, so it was pure duplication. Use
  `npm run tauri build` for an ad-hoc local installer, or push a `vX.Y.Z` tag
  to have CI build and publish one for every platform.

### [4.2.0] — 2026-07-23

#### Added
- **In-app User Manual** — a new panel (book icon in the header, or accessible
  any time alongside the AI Assistant) with a quick reference for downloading,
  converting, cookie-gated sites, the Run Log, the AI Assistant, and language/
  theme switching, plus links to the full Wiki and issue tracker. Available in
  all three languages and reacts instantly to the language switcher, just like
  the rest of the UI.

### [4.1.1] — 2026-07-22

#### Fixed
- **Desktop app freezing / "Not Responding"** — the download, convert, batch
  queue, and AI-plan commands ran synchronously on the main UI thread (Tauri
  runs non-`async` commands there), so any operation lasting more than a few
  seconds starved the window's message loop and triggered the OS's "Not
  Responding" state. These commands now run on a background thread
  (`tauri::async_runtime::spawn_blocking`), keeping the window responsive for
  the whole operation. As a side effect, the **Stop button** now reacts
  immediately during long operations instead of queuing behind them.

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
generation of the app: `Version/Version3.0/CHANGELOG.md`.

---

## 繁體中文

### [4.2.2] — 2026-07-23

#### 新增
- **清空運行日誌前加確認** — 點擊「清空」現在會先詢問確認，不會再一鍵就把
  日誌直接清光、無法復原（如果需要保留，請先匯出）。
- 頁首語言選單旁加了一個語言圖示。

#### 變更
- CI 現在會在每次 push 到 `main` 時跑完整測試套件（63 項 Python 測試、
  `svelte-check`、`cargo check`／`clippy`），在問題進到正式發布前先攔下來。
  不影響 App 本身。

### [4.2.1] — 2026-07-23

#### 修復
- **語言下拉選單顯示原始代碼而非名稱**（顯示 `en`／`zh_tw`／`zh_cn` 而非
  「English」／「繁體中文」／「简体中文」）——由
  [#4](https://github.com/SpaceSquare640/Multimedia_Downloader/issues/4) 回報。
  原因是顯示名稱要跑一趟引擎 sidecar 才能拿到，一旦這趟呼叫失敗，下拉選單
  會悄悄退回顯示原始代碼、不會有任何錯誤提示。修法：改成直接從建置時期就
  綁進 app 的語言檔讀取名稱——完全不依賴後端，不會再發生這個問題。

#### 變更
- 移除純本機專用的 `packaging/build-desktop.ps1` 腳本，以及呼叫它的
  `package` npm script——CI 的發布流程有自己等效的步驟、從未用過這個檔案，
  純屬重複。想在本機直接建置安裝檔可用 `npm run tauri build`；正式發布則
  推送 `vX.Y.Z` tag 讓 CI 自動建置各平台並發布。

### [4.2.0] — 2026-07-23

#### 新增
- **App 內建使用手冊** — 新增一個面板（點頁首書本圖示開啟，跟 AI 助手一樣隨
  時可用），快速說明下載、轉換、需登入平台、運行日誌、AI 助手、語言/主題切
  換等用法，並附上完整 Wiki 與 Issue 回報連結的網址。支援三語，語言切換時內
  容會即時跟著變。

### [4.1.1] — 2026-07-22

#### 修復
- **桌面版容易凍結／「沒有回應」** — 下載、轉換、批次佇列、AI 規劃這幾個
  指令原本同步跑在主 UI 執行緒上（Tauri 對非 async 指令就是這樣處理），只要
  操作超過幾秒，視窗的訊息迴圈就會被卡住，觸發作業系統的「沒有回應」狀態。
  現在這些指令改到背景執行緒執行（`tauri::async_runtime::spawn_blocking`），
  整個操作期間視窗都能保持回應。附帶效果：長時間操作中**「停止」按鈕**現在
  會立即反應，不會再排在後面等。

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
`Version/Version3.0/CHANGELOG.md`。

---

## 简体中文

### [4.2.2] — 2026-07-23

#### 新增
- **清空运行日志前加确认** — 点击「清空」现在会先询问确认，不会再一键就把
  日志直接清空、无法恢复（如果需要保留，请先导出）。
- 页首语言选单旁加了一个语言图标。

#### 变更
- CI 现在会在每次 push 到 `main` 时跑完整测试套件（63 项 Python 测试、
  `svelte-check`、`cargo check`／`clippy`），在问题进入正式发布前先拦下来。
  不影响 App 本身。

### [4.2.1] — 2026-07-23

#### 修复
- **语言下拉菜单显示原始代码而非名称**（显示 `en`／`zh_tw`／`zh_cn` 而非
  「English」／「繁體中文」／「简体中文」）——由
  [#4](https://github.com/SpaceSquare640/Multimedia_Downloader/issues/4) 反馈。
  原因是显示名称要跑一趟引擎 sidecar 才能拿到，一旦这趟调用失败，下拉菜单
  会悄悄退回显示原始代码、不会有任何错误提示。修复方式：改成直接从构建时
  就绑进 app 的语言文件读取名称——完全不依赖后端，不会再发生这个问题。

#### 变更
- 移除纯本机专用的 `packaging/build-desktop.ps1` 脚本，以及调用它的
  `package` npm script——CI 的发布流程有自己等效的步骤、从未用过这个文件，
  纯属重复。想在本机直接构建安装包可用 `npm run tauri build`；正式发布则
  推送 `vX.Y.Z` tag 让 CI 自动构建各平台并发布。

### [4.2.0] — 2026-07-23

#### 新增
- **App 内置使用手册** — 新增一个面板（点页首书本图标打开，跟 AI 助手一样随
  时可用），快速说明下载、转换、需登录平台、运行日志、AI 助手、语言/主题切
  换等用法，并附上完整 Wiki 与 Issue 反馈链接的网址。支持三语，切换语言时内
  容会即时跟着变。

### [4.1.1] — 2026-07-22

#### 修复
- **桌面版容易冻结／「未响应」** — 下载、转换、批次队列、AI 规划这几个指令
  原本同步运行在主 UI 线程上（Tauri 对非 async 指令就是这样处理），只要操作
  超过几秒，窗口的消息循环就会被卡住，触发操作系统的「未响应」状态。现在这
  些指令改到后台线程执行（`tauri::async_runtime::spawn_blocking`），整个操
  作期间窗口都能保持响应。附带效果：长时间操作中**「停止」按钮**现在会立即
  响应，不会再排在后面等。

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
`Version/Version3.0/CHANGELOG.md`。
