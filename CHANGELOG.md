# Changelog

**Language / 語言 / 语言:** [English](#english) · [繁體中文](#繁體中文) · [简体中文](#简体中文)

---

## English

### [3.0.0] — 2026-05-27

#### Added
- **Web app (`web_app.py`)** — Flask-based browser interface. Run locally or
  deploy to any WSGI host. Includes JSON API, per-job progress polling, and a
  shared dark theme matching the desktop GUI.
- **Tri-language UI** — English (default), Traditional Chinese, Simplified
  Chinese. Switch at runtime; both interfaces share `i18n.py`.
- **Shared engine (`core.py`)** — extracted yt-dlp + ffmpeg logic into a
  UI-agnostic `Downloader` / `Converter` pair so the desktop GUI and web app
  reuse the exact same code path.

#### Changed
- **English-first interface** — all UI text, log lines, and dialog messages
  now default to English; the previous bilingual labels are replaced by a
  language switcher.
- **Cleaner architecture** — desktop GUI shrunk by factoring the engine out,
  leaving the file focused on layout + tkinter glue.
- **Format string handling** — log messages use keyed templates resolved
  through `Translator.t(key, **fmt)` so adding languages no longer requires
  editing core logic.

#### Improved
- Cooperative stop now reliably interrupts both downloads and conversions via
  `Downloader.stop()` / `Converter.stop()` on the shared engine.
- Progress callbacks now report percent, speed, and ETA as a typed tuple
  instead of stringly-typed config calls.
- `format_filesize()` extended to GB and keeps the 1 MiB boundary fix.
- Conversion status cells in the desktop tree now re-translate when the
  language is switched mid-session.

### [2.4.0] — Previous
- Bilingual (Chinese + English) hard-coded UI.
- Session log auto-save with timestamped filenames.
- Cookie support via browser auto-read or Netscape `cookies.txt`.

### [2.0.0 → 2.3.0]
- Cookie support, log saving, mouse-wheel scrolling, status tree, batch URL
  download with progress per item.

### [1.0.0]
- Initial desktop GUI with single-URL download via yt-dlp.

---

## 繁體中文

### [3.0.0] — 2026-05-27

#### 新增
- **網頁版（`web_app.py`）** — 以 Flask 為基礎的瀏覽器介面。可在本機執行
  或部署至任意 WSGI 主機。提供 JSON API、單一任務進度輪詢，與桌面版一致
  的深色主題。
- **三語介面** — 英文（預設）、繁體中文、簡體中文，可即時切換。兩種介面
  共用 `i18n.py`。
- **共用引擎（`core.py`）** — 將 yt-dlp 與 ffmpeg 邏輯抽出為與介面無關的
  `Downloader` / `Converter`，桌面版與網頁版完全共用同一段下載程式。

#### 變更
- **英文為預設介面** — 所有 UI 文字、日誌、對話框預設英文，原本的中英雙語
  混合改為語言切換器。
- **更清晰的架構** — 桌面版將下載引擎抽出後變得更精簡，專注於版面配置與
  tkinter 連動。
- **格式化字串處理** — 日誌訊息改用帶 key 的模板，透過
  `Translator.t(key, **fmt)` 解析，未來新增語言無需改動核心程式。

#### 改善
- 透過共用引擎的 `Downloader.stop()` / `Converter.stop()`，可協同式中斷
  下載或轉換。
- 進度回呼以型別化的 `(percent, speed, eta)` 三元組傳遞，取代過去以字串
  config 的處理。
- `format_filesize()` 擴充到 GB，並保留 1 MiB 邊界修正。
- 桌面版檔案列表的狀態欄會在語言切換時自動重新翻譯。

### [2.4.0] — 先前版本
- 寫死的中英雙語介面。
- 帶時間戳的日誌自動儲存。
- Cookie 支援（自動讀取瀏覽器或 Netscape `cookies.txt`）。

### [2.0.0 → 2.3.0]
- Cookie 支援、日誌儲存、滑鼠滾輪捲動、狀態列、批量下載逐項進度。

### [1.0.0]
- 桌面版初版，單一 URL 下載。

---

## 简体中文

### [3.0.0] — 2026-05-27

#### 新增
- **网页版（`web_app.py`）** — 基于 Flask 的浏览器界面。可在本机运行或
  部署到任意 WSGI 主机。提供 JSON API、单任务进度轮询，以及与桌面版一致
  的深色主题。
- **三语界面** — 英文（默认）、繁体中文、简体中文，可即时切换。两种界面
  共用 `i18n.py`。
- **共享引擎（`core.py`）** — 将 yt-dlp 与 ffmpeg 逻辑抽出为与界面无关的
  `Downloader` / `Converter`，桌面版与网页版完全共用同一段下载代码。

#### 变更
- **英文为默认界面** — 所有 UI 文本、日志、对话框默认英文，原来的中英双语
  混合改为语言切换器。
- **更清晰的架构** — 桌面版抽出下载引擎后更精简，专注于布局与 tkinter
  连接。
- **格式化字符串处理** — 日志消息改用带 key 的模板，通过
  `Translator.t(key, **fmt)` 解析，未来新增语言无需改动核心代码。

#### 改善
- 通过共享引擎的 `Downloader.stop()` / `Converter.stop()`，可协作式中断
  下载或转换。
- 进度回调以类型化的 `(percent, speed, eta)` 三元组传递，取代过去以字符串
  config 的处理方式。
- `format_filesize()` 扩展到 GB，并保留 1 MiB 边界修复。
- 桌面版文件列表的状态栏会在语言切换时自动重新翻译。

### [2.4.0] — 先前版本
- 写死的中英双语界面。
- 带时间戳的日志自动保存。
- Cookie 支持（自动读取浏览器或 Netscape `cookies.txt`）。

### [2.0.0 → 2.3.0]
- Cookie 支持、日志保存、鼠标滚轮滚动、状态栏、批量下载逐项进度。

### [1.0.0]
- 桌面版初版，单 URL 下载。
