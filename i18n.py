"""
Internationalization (i18n) module for Multimedia Downloader.

Supports three languages — default is English:
    en     : English
    zh_tw  : Traditional Chinese (繁體中文)
    zh_cn  : Simplified Chinese  (简体中文)

Usage
-----
    from i18n import Translator
    tr = Translator("en")
    print(tr.t("app_title"))
    tr.set_language("zh_tw")
    print(tr.t("app_title"))

All UI surfaces (desktop GUI and web app) share this module so the three
language variants stay in lockstep across the project.
"""

from __future__ import annotations

DEFAULT_LANG = "en"

LANG_DISPLAY: dict[str, str] = {
    "en":    "English",
    "zh_tw": "繁體中文",
    "zh_cn": "简体中文",
}
LANG_CODE_FROM_DISPLAY: dict[str, str] = {v: k for k, v in LANG_DISPLAY.items()}


# ─────────────────────────────────────────────────────────────────────────────
#  Translation strings.  Missing keys fall back to English, then to the raw key.
# ─────────────────────────────────────────────────────────────────────────────

STRINGS: dict[str, dict[str, str]] = {

    # ╭─────────────────────────── English (default) ───────────────────────────╮
    "en": {
        "app_title":            "Multimedia Downloader",
        "app_subtitle":         "YouTube · Facebook · Instagram · TikTok · BiliBili · 500+ platforms",
        "language":             "Language",

        # Tabs
        "tab_download":         "  ⬇  Download  ",
        "tab_convert":          "  🔄  Convert  ",

        # Section headers
        "sec_mode":             "Download Mode",
        "sec_format":           "Output Format",
        "sec_urls":             "URLs  (one per line · batch supported)",
        "sec_save":             "Save Location",
        "sec_cookie":           "🍪  Cookie Settings  (Douyin / Instagram / etc.)",
        "sec_log":              "📄  Log Settings",

        # Mode radio
        "mode_video":           "🎬  Video",
        "mode_audio":           "🎵  Audio",

        # Format row
        "lbl_video_fmt":        "Video format:",
        "lbl_audio_fmt":        "Audio format:",
        "lbl_quality":          "Quality:",

        # URL panel
        "btn_clear":            "Clear",
        "btn_paste":            "Paste",
        "urls_caption":         "Supports: YouTube · Facebook · Instagram · TikTok · BiliBili · Twitter · SoundCloud · Twitch · Vimeo · 500+",

        # Save location
        "btn_browse":           "Browse",

        # Cookie
        "cookie_warning":       "Douyin, private TikTok / Instagram and similar platforms require cookies to download.",
        "cookie_m1":            "Method 1 — From browser:",
        "cookie_m1_hint":       "← Select the browser you are signed in with",
        "cookie_m2":            "Method 2 — Cookie file path (cookies.txt):",
        "cookie_export_hint":   ("💡  How to export cookies.txt:\n"
                                 "   Chrome / Edge / Brave: install \"Get cookies.txt LOCALLY\" extension → open the site → Export\n"
                                 "   Firefox: install the \"cookies.txt\" extension → Export\n"
                                 "   Or just pick a browser above and yt-dlp will read its cookies directly (requires being signed in)."),

        # Log settings
        "log_auto_toggle":      "📄  Auto-save log after each download session",
        "log_save_dir":         "Log save directory:",
        "log_fmt_note":         "💡  Log will be saved as download_log_YYYYMMDD_HHMMSS.txt in the selected directory.",

        # Action buttons
        "btn_start_download":   "⬇  Start Download",
        "btn_stop":             "✕  Stop",
        "btn_start_convert":    "🔄  Start Convert",
        "btn_save_log_now":     "📄  Save Log Now",

        # Status / progress
        "status_ready_dl":      "Ready",
        "status_ready_cv":      "Ready",
        "status_downloading":   "Downloading ({n}/{t}): {url}",
        "status_progress":      "Downloading {pct}%  ·  Speed {speed}  ·  ETA {eta}",
        "status_all_done_dl":   "✓  All {t} done!",
        "status_converting":    "Converting ({n}/{t}): {file}",
        "status_all_done_cv":   "✓  All {t} file(s) converted.",

        # Log title
        "log_title":            "Log",

        # Convert tab
        "cv_format":            "Conversion Format",
        "cv_from":              "From:",
        "cv_to":                "   →   To:",
        "cv_file_list":         "File List",
        "btn_add_files":        "+  Add Files",
        "btn_add_folder":       "+  Add Folder",
        "btn_remove_selected":  "✕  Remove Selected",
        "col_filename":         "Filename",
        "col_size":             "Size",
        "col_status":           "Status",
        "cv_output":            "Output Location",
        "cv_ffmpeg_notice":     "⚠  Conversion requires ffmpeg installed and added to PATH.  →  https://ffmpeg.org",

        # Treeview status cells
        "tree_pending":         "⏳  Pending",
        "tree_converting":      "🔄  Converting…",
        "tree_done":            "✓  Done",
        "tree_error":           "✗  Error",
        "tree_need_ffmpeg":     "✗  Needs ffmpeg",

        # Dialogs — titles
        "dlg_select_save":      "Select Save Location",
        "dlg_select_cookie":    "Select cookies.txt",
        "dlg_select_files":     "Select files to convert",
        "dlg_select_folder":    "Select Folder",
        "ft_cookie":            "Cookie file",
        "ft_media":             "Media files",
        "ft_all":               "All files",

        # Message boxes
        "msg_no_url_title":     "No URL",
        "msg_no_url_body":      "Please enter at least one URL.",
        "msg_bad_path_title":   "Path Error",
        "msg_bad_path_body":    "Save path does not exist:\n{path}",
        "msg_no_files_title":   "No Files",
        "msg_no_files_body":    "Please add files first.",
        "msg_same_fmt_title":   "Same Format",
        "msg_same_fmt_body":    "Source and destination formats are the same.",
        "msg_log_empty_title":  "Log Empty",
        "msg_log_empty_body":   "No log entries to save. Please run a download first.",

        # Log lines
        "log_start_batch":      "▶  Starting {n} download(s)…",
        "log_item_downloading": "[{i}/{t}]  Downloading: {url}",
        "log_item_done":        "[{i}/{t}]  ✓  Done",
        "log_item_error":       "[{i}/{t}]  ✗  Error: {err}",
        "log_all_done":         "✓  All {t} tasks finished.",
        "log_stopped_dl":       "⛔  Download stopped.",
        "log_stopping":         "⚠  Stopping…",
        "log_cookie_file":      "🍪  Using cookie file: {name}",
        "log_cookie_browser":   "🍪  Reading cookies from browser: {browser}",
        "log_convert_start":    "[{i}/{t}]  🔄  {src}  →  {dst}",
        "log_convert_done":     "[{i}/{t}]  ✓  Done: {name}",
        "log_convert_error":    "[{i}/{t}]  ✗  Error: {err}",
        "log_no_ffmpeg":        "[{i}/{t}]  ✗  ffmpeg not found — install from https://ffmpeg.org",
        "log_convert_stopped":  "⛔  Conversion stopped.",
        "log_all_converted":    "✓  All {t} conversions done.",
        "log_save_failed_dir":  "⚠  Log save failed: directory not found — {path}",
        "log_save_failed":      "⚠  Log save failed: {err}",
        "log_saved":            "📄  Log saved → {name}",

        # Log file header
        "log_file_header":      "Multimedia Downloader — Download Log",
        "log_file_generated":   "Generated: {ts}",
        "log_file_end":         "End of log — {n} line(s)",

        # Web-only
        "web_url_placeholder":  "Paste one or more URLs (one per line)…",
        "web_no_jobs":          "No active downloads.",
        "web_job_pending":      "Pending",
        "web_job_running":      "Downloading",
        "web_job_done":         "Done",
        "web_job_error":        "Error",
        "web_open_local":       "Open download folder on server",
        "web_download_file":    "Download file",
        "web_settings":         "Settings",
        "web_clear_completed":  "Clear completed",
        "web_footer":           "Multimedia Downloader · Run locally or deploy online",
    },

    # ╭───────────────────────── Traditional Chinese ───────────────────────────╮
    "zh_tw": {
        "app_title":            "多媒體下載器",
        "app_subtitle":         "YouTube · Facebook · Instagram · TikTok · BiliBili · 500+ 平台",
        "language":             "語言",

        "tab_download":         "  ⬇  下載  ",
        "tab_convert":          "  🔄  轉換  ",

        "sec_mode":             "下載模式",
        "sec_format":           "輸出格式",
        "sec_urls":             "影片連結（每行一個 · 支援批量）",
        "sec_save":             "存放位置",
        "sec_cookie":           "🍪  Cookie 設定（抖音 / Instagram 等）",
        "sec_log":              "📄  日誌設定",

        "mode_video":           "🎬  影片",
        "mode_audio":           "🎵  音樂 / 音頻",

        "lbl_video_fmt":        "影片格式：",
        "lbl_audio_fmt":        "音頻格式：",
        "lbl_quality":          "畫質：",

        "btn_clear":            "清除",
        "btn_paste":            "貼上",
        "urls_caption":         "支援：YouTube · Facebook · Instagram · TikTok · BiliBili · Twitter · SoundCloud · Twitch · Vimeo · 500+",

        "btn_browse":           "瀏覽",

        "cookie_warning":       "抖音、TikTok 登入版、Instagram 私人帳號等平台需要 Cookie 才能下載。",
        "cookie_m1":            "方法一 — 從瀏覽器讀取：",
        "cookie_m1_hint":       "← 選擇你已登入的瀏覽器",
        "cookie_m2":            "方法二 — Cookie 檔案路徑（cookies.txt）：",
        "cookie_export_hint":   ("💡  如何匯出 cookies.txt：\n"
                                 "   Chrome / Edge / Brave：安裝「Get cookies.txt LOCALLY」擴充功能 → 在網站頁面點 Export\n"
                                 "   Firefox：安裝「cookies.txt」擴充功能 → Export\n"
                                 "   或直接在上方選擇瀏覽器讓 yt-dlp 自動讀取（需在該瀏覽器登入）。"),

        "log_auto_toggle":      "📄  下載完成後自動儲存日誌",
        "log_save_dir":         "日誌存放目錄：",
        "log_fmt_note":         "💡  日誌將以 download_log_YYYYMMDD_HHMMSS.txt 格式儲存於所選目錄。",

        "btn_start_download":   "⬇  開始下載",
        "btn_stop":             "✕  停止",
        "btn_start_convert":    "🔄  開始轉換",
        "btn_save_log_now":     "📄  立即儲存日誌",

        "status_ready_dl":      "等待下載⋯",
        "status_ready_cv":      "等待轉換⋯",
        "status_downloading":   "下載中（{n}/{t}）：{url}",
        "status_progress":      "下載中 {pct}%  ·  速度 {speed}  ·  ETA {eta}",
        "status_all_done_dl":   "✓  全部 {t} 項已完成！",
        "status_converting":    "轉換中（{n}/{t}）：{file}",
        "status_all_done_cv":   "✓  全部 {t} 個檔案已轉換完成。",

        "log_title":            "下載日誌",

        "cv_format":            "轉換格式",
        "cv_from":              "來源：",
        "cv_to":                "   →   目標：",
        "cv_file_list":         "檔案列表",
        "btn_add_files":        "+  加入檔案",
        "btn_add_folder":       "+  加入資料夾",
        "btn_remove_selected":  "✕  移除選取",
        "col_filename":         "檔案名稱",
        "col_size":             "大小",
        "col_status":           "狀態",
        "cv_output":            "輸出位置",
        "cv_ffmpeg_notice":     "⚠  轉換功能需要安裝 ffmpeg 並加入系統 PATH。  →  https://ffmpeg.org",

        "tree_pending":         "⏳  等待中",
        "tree_converting":      "🔄  轉換中⋯",
        "tree_done":            "✓  完成",
        "tree_error":           "✗  錯誤",
        "tree_need_ffmpeg":     "✗  需要 ffmpeg",

        "dlg_select_save":      "選擇存放位置",
        "dlg_select_cookie":    "選擇 cookies.txt",
        "dlg_select_files":     "選擇要轉換的檔案",
        "dlg_select_folder":    "選擇資料夾",
        "ft_cookie":            "Cookie 檔案",
        "ft_media":             "媒體檔案",
        "ft_all":               "所有檔案",

        "msg_no_url_title":     "無 URL",
        "msg_no_url_body":      "請輸入至少一個下載連結！",
        "msg_bad_path_title":   "路徑錯誤",
        "msg_bad_path_body":    "存放路徑不存在：\n{path}",
        "msg_no_files_title":   "無檔案",
        "msg_no_files_body":    "請先加入要轉換的檔案！",
        "msg_same_fmt_title":   "格式相同",
        "msg_same_fmt_body":    "來源格式與目標格式相同，無需轉換！",
        "msg_log_empty_title":  "日誌為空",
        "msg_log_empty_body":   "目前沒有日誌可以儲存。請先執行下載。",

        "log_start_batch":      "▶  開始下載 {n} 個連結⋯",
        "log_item_downloading": "[{i}/{t}]  下載中：{url}",
        "log_item_done":        "[{i}/{t}]  ✓  完成",
        "log_item_error":       "[{i}/{t}]  ✗  錯誤：{err}",
        "log_all_done":         "✓  全部 {t} 個任務完成。",
        "log_stopped_dl":       "⛔  下載已停止。",
        "log_stopping":         "⚠  正在停止⋯",
        "log_cookie_file":      "🍪  使用 Cookie 檔案：{name}",
        "log_cookie_browser":   "🍪  從瀏覽器讀取 Cookie：{browser}",
        "log_convert_start":    "[{i}/{t}]  🔄  {src}  →  {dst}",
        "log_convert_done":     "[{i}/{t}]  ✓  完成：{name}",
        "log_convert_error":    "[{i}/{t}]  ✗  錯誤：{err}",
        "log_no_ffmpeg":        "[{i}/{t}]  ✗  找不到 ffmpeg — 請至 https://ffmpeg.org 下載",
        "log_convert_stopped":  "⛔  轉換已停止。",
        "log_all_converted":    "✓  全部 {t} 個轉換完成。",
        "log_save_failed_dir":  "⚠  日誌儲存失敗：目錄不存在 — {path}",
        "log_save_failed":      "⚠  日誌儲存失敗：{err}",
        "log_saved":            "📄  日誌已儲存 → {name}",

        "log_file_header":      "多媒體下載器 — 下載日誌",
        "log_file_generated":   "產生時間：{ts}",
        "log_file_end":         "日誌結束 — 共 {n} 行",

        "web_url_placeholder":  "貼上一個或多個 URL（每行一個）⋯",
        "web_no_jobs":          "目前沒有進行中的下載。",
        "web_job_pending":      "等待中",
        "web_job_running":      "下載中",
        "web_job_done":         "完成",
        "web_job_error":        "錯誤",
        "web_open_local":       "打開伺服器下載資料夾",
        "web_download_file":    "下載檔案",
        "web_settings":         "設定",
        "web_clear_completed":  "清除已完成",
        "web_footer":           "多媒體下載器 · 可本機執行或部署於線上",
    },

    # ╭───────────────────────── Simplified Chinese ────────────────────────────╮
    "zh_cn": {
        "app_title":            "多媒体下载器",
        "app_subtitle":         "YouTube · Facebook · Instagram · TikTok · BiliBili · 500+ 平台",
        "language":             "语言",

        "tab_download":         "  ⬇  下载  ",
        "tab_convert":          "  🔄  转换  ",

        "sec_mode":             "下载模式",
        "sec_format":           "输出格式",
        "sec_urls":             "视频链接（每行一个 · 支持批量）",
        "sec_save":             "存放位置",
        "sec_cookie":           "🍪  Cookie 设置（抖音 / Instagram 等）",
        "sec_log":              "📄  日志设置",

        "mode_video":           "🎬  视频",
        "mode_audio":           "🎵  音乐 / 音频",

        "lbl_video_fmt":        "视频格式：",
        "lbl_audio_fmt":        "音频格式：",
        "lbl_quality":          "画质：",

        "btn_clear":            "清除",
        "btn_paste":            "粘贴",
        "urls_caption":         "支持：YouTube · Facebook · Instagram · TikTok · BiliBili · Twitter · SoundCloud · Twitch · Vimeo · 500+",

        "btn_browse":           "浏览",

        "cookie_warning":       "抖音、TikTok 登录版、Instagram 私人账号等平台需要 Cookie 才能下载。",
        "cookie_m1":            "方法一 — 从浏览器读取：",
        "cookie_m1_hint":       "← 选择你已登录的浏览器",
        "cookie_m2":            "方法二 — Cookie 文件路径（cookies.txt）：",
        "cookie_export_hint":   ("💡  如何导出 cookies.txt：\n"
                                 "   Chrome / Edge / Brave：安装「Get cookies.txt LOCALLY」扩展 → 在网站页面点 Export\n"
                                 "   Firefox：安装「cookies.txt」扩展 → Export\n"
                                 "   或直接在上方选择浏览器让 yt-dlp 自动读取（需在该浏览器中登录）。"),

        "log_auto_toggle":      "📄  下载完成后自动保存日志",
        "log_save_dir":         "日志保存目录：",
        "log_fmt_note":         "💡  日志将以 download_log_YYYYMMDD_HHMMSS.txt 格式保存于所选目录。",

        "btn_start_download":   "⬇  开始下载",
        "btn_stop":             "✕  停止",
        "btn_start_convert":    "🔄  开始转换",
        "btn_save_log_now":     "📄  立即保存日志",

        "status_ready_dl":      "等待下载⋯",
        "status_ready_cv":      "等待转换⋯",
        "status_downloading":   "下载中（{n}/{t}）：{url}",
        "status_progress":      "下载中 {pct}%  ·  速度 {speed}  ·  ETA {eta}",
        "status_all_done_dl":   "✓  全部 {t} 项已完成！",
        "status_converting":    "转换中（{n}/{t}）：{file}",
        "status_all_done_cv":   "✓  全部 {t} 个文件已转换完成。",

        "log_title":            "下载日志",

        "cv_format":            "转换格式",
        "cv_from":              "来源：",
        "cv_to":                "   →   目标：",
        "cv_file_list":         "文件列表",
        "btn_add_files":        "+  添加文件",
        "btn_add_folder":       "+  添加文件夹",
        "btn_remove_selected":  "✕  移除选中",
        "col_filename":         "文件名",
        "col_size":             "大小",
        "col_status":           "状态",
        "cv_output":            "输出位置",
        "cv_ffmpeg_notice":     "⚠  转换功能需要安装 ffmpeg 并加入系统 PATH。  →  https://ffmpeg.org",

        "tree_pending":         "⏳  等待中",
        "tree_converting":      "🔄  转换中⋯",
        "tree_done":            "✓  完成",
        "tree_error":           "✗  错误",
        "tree_need_ffmpeg":     "✗  需要 ffmpeg",

        "dlg_select_save":      "选择存放位置",
        "dlg_select_cookie":    "选择 cookies.txt",
        "dlg_select_files":     "选择要转换的文件",
        "dlg_select_folder":    "选择文件夹",
        "ft_cookie":            "Cookie 文件",
        "ft_media":             "媒体文件",
        "ft_all":               "所有文件",

        "msg_no_url_title":     "无 URL",
        "msg_no_url_body":      "请输入至少一个下载链接！",
        "msg_bad_path_title":   "路径错误",
        "msg_bad_path_body":    "存放路径不存在：\n{path}",
        "msg_no_files_title":   "无文件",
        "msg_no_files_body":    "请先添加要转换的文件！",
        "msg_same_fmt_title":   "格式相同",
        "msg_same_fmt_body":    "源格式与目标格式相同，无需转换！",
        "msg_log_empty_title":  "日志为空",
        "msg_log_empty_body":   "目前没有日志可以保存。请先执行下载。",

        "log_start_batch":      "▶  开始下载 {n} 个链接⋯",
        "log_item_downloading": "[{i}/{t}]  下载中：{url}",
        "log_item_done":        "[{i}/{t}]  ✓  完成",
        "log_item_error":       "[{i}/{t}]  ✗  错误：{err}",
        "log_all_done":         "✓  全部 {t} 个任务完成。",
        "log_stopped_dl":       "⛔  下载已停止。",
        "log_stopping":         "⚠  正在停止⋯",
        "log_cookie_file":      "🍪  使用 Cookie 文件：{name}",
        "log_cookie_browser":   "🍪  从浏览器读取 Cookie：{browser}",
        "log_convert_start":    "[{i}/{t}]  🔄  {src}  →  {dst}",
        "log_convert_done":     "[{i}/{t}]  ✓  完成：{name}",
        "log_convert_error":    "[{i}/{t}]  ✗  错误：{err}",
        "log_no_ffmpeg":        "[{i}/{t}]  ✗  找不到 ffmpeg — 请到 https://ffmpeg.org 下载",
        "log_convert_stopped":  "⛔  转换已停止。",
        "log_all_converted":    "✓  全部 {t} 个转换完成。",
        "log_save_failed_dir":  "⚠  日志保存失败：目录不存在 — {path}",
        "log_save_failed":      "⚠  日志保存失败：{err}",
        "log_saved":            "📄  日志已保存 → {name}",

        "log_file_header":      "多媒体下载器 — 下载日志",
        "log_file_generated":   "生成时间：{ts}",
        "log_file_end":         "日志结束 — 共 {n} 行",

        "web_url_placeholder":  "粘贴一个或多个 URL（每行一个）⋯",
        "web_no_jobs":          "目前没有进行中的下载。",
        "web_job_pending":      "等待中",
        "web_job_running":      "下载中",
        "web_job_done":         "完成",
        "web_job_error":        "错误",
        "web_open_local":       "打开服务器下载文件夹",
        "web_download_file":    "下载文件",
        "web_settings":         "设置",
        "web_clear_completed":  "清除已完成",
        "web_footer":           "多媒体下载器 · 可本机运行或部署到线上",
    },
}


class Translator:
    """
    Lightweight runtime translator.

    Falls back gracefully on missing keys: requested lang → English → raw key.
    Use ``tr.t(key, **kwargs)`` for templated strings; ``.format(**kwargs)``
    is applied when ``kwargs`` is non-empty.
    """

    def __init__(self, lang: str = DEFAULT_LANG) -> None:
        self.lang = lang if lang in STRINGS else DEFAULT_LANG

    # ── Lookup ────────────────────────────────────────────────────────────────
    def t(self, key: str, **kwargs) -> str:
        s = STRINGS.get(self.lang, {}).get(key)
        if s is None:
            s = STRINGS[DEFAULT_LANG].get(key, key)
        return s.format(**kwargs) if kwargs else s

    # ── Mutation ──────────────────────────────────────────────────────────────
    def set_language(self, lang: str) -> bool:
        """Set active language. Returns True if accepted, False otherwise."""
        if lang in STRINGS:
            self.lang = lang
            return True
        return False

    @staticmethod
    def available() -> dict[str, str]:
        """Return mapping of language code → display label."""
        return dict(LANG_DISPLAY)
