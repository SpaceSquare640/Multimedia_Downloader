#!/usr/bin/env python3
# =============================================================================
#  Multimedia Downloader — Desktop GUI
#  Version : 3.0
#  Tested  : Python 3.8+ · Windows / macOS / Linux
#
#  A tkinter-based desktop client that wraps ``core.Downloader`` and
#  ``core.Converter``. Translations live in ``i18n.py`` and are switchable at
#  runtime from the language menu in the top-right corner.  Default is English.
#
#  Features
#  --------
#    * Batch URL download via yt-dlp (YouTube, TikTok, Bilibili, 500+ sites)
#    * Audio extraction + format conversion (requires ffmpeg)
#    * Cookie support (browser-direct or Netscape cookies.txt file)
#    * Optional auto-save of session log
#    * Tri-language UI (English / Traditional Chinese / Simplified Chinese)
#
#  Dependencies (auto-installed on first launch)
#  ---------------------------------------------
#      yt-dlp · requests · Pillow
#  Optional: ffmpeg in PATH (https://ffmpeg.org) for audio & conversion.
# =============================================================================


# ─────────────────────────────────────────────────────────────────────────────
#  SECTION 1 ── Bootstrap
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
import subprocess
import importlib


_MIN_PYTHON = (3, 8)


def _check_python_version() -> None:
    """Ensure the running interpreter meets the minimum required version."""
    cur = sys.version_info[:2]
    if cur < _MIN_PYTHON:
        print(
            f"[ERROR] Python {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]}+ required. "
            f"Current: {cur[0]}.{cur[1]}"
        )
        sys.exit(1)
    print(f"[OK] Python {cur[0]}.{cur[1]}.{sys.version_info[2]} detected")


_REQUIRED: dict[str, str] = {
    "yt_dlp":   "yt-dlp",
    "PIL":      "Pillow",
    "requests": "requests",
}


def _ensure_packages() -> None:
    """Verify required packages are present; install any that are missing."""
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("[WARN] tkinter not found. On Debian/Ubuntu: sudo apt install python3-tk")

    missing: list[str] = []
    for module, pip_name in _REQUIRED.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"[..] Installing: {', '.join(missing)}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", *missing]
        )

    # Best-effort silent upgrade of yt-dlp — extractor support changes daily.
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


_check_python_version()
_ensure_packages()


# ─────────────────────────────────────────────────────────────────────────────
#  SECTION 2 ── Imports
# ─────────────────────────────────────────────────────────────────────────────

import queue
import threading
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from core import (
    AUDIO_FORMATS, BROWSERS, QUALITY_PRESETS, VIDEO_FORMATS,
    Converter, Downloader, DownloadOptions,
    format_filesize,
)
from i18n import LANG_CODE_FROM_DISPLAY, LANG_DISPLAY, Translator


# ─────────────────────────────────────────────────────────────────────────────
#  SECTION 3 ── Constants
# ─────────────────────────────────────────────────────────────────────────────

APP_VERSION = "3.0"

# Dark theme palette — central so retheming touches one place.
DARK: dict[str, str] = {
    "bg":         "#0d1117",
    "surface":    "#161b22",
    "surface2":   "#21262d",
    "border":     "#30363d",
    "accent":     "#58a6ff",
    "accent2":    "#3fb950",
    "warn":       "#d29922",
    "danger":     "#f85149",
    "text":       "#e6edf3",
    "text_dim":   "#8b949e",
    "text_muted": "#484f58",
    "input_bg":   "#0d1117",
    "progress":   "#1f6feb",
}

DEFAULT_SAVE_PATH: str = str(Path.home() / "Desktop")
if not os.path.exists(DEFAULT_SAVE_PATH):
    DEFAULT_SAVE_PATH = str(Path.home())


# ─────────────────────────────────────────────────────────────────────────────
#  SECTION 4 ── Main Application
# ─────────────────────────────────────────────────────────────────────────────

class MultimediaDownloader(tk.Tk):
    """
    Main desktop window.

    Subclassing :class:`tk.Tk` directly avoids a redundant ``root = Tk()``
    intermediary. Translations are looked up through :attr:`tr` and the UI
    fully rebuilds itself when the language is changed.
    """

    # ── 4a · Initialisation ───────────────────────────────────────────────────

    def __init__(self) -> None:
        super().__init__()

        # i18n  --------------------------------------------------------------
        self.tr = Translator("en")                       # default language
        self.lang_var = tk.StringVar(value=LANG_DISPLAY["en"])

        # Window geometry — open at 85 % of screen, centred, with a min size.
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = max(900, int(sw * 0.85)), max(640, int(sh * 0.85))
        x, y = (sw - w) // 2, (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(900, 640)
        self.configure(bg=DARK["bg"])
        self._sync_title()

        # State vars  --------------------------------------------------------
        self.save_path       = tk.StringVar(value=DEFAULT_SAVE_PATH)
        self.cv_save_path    = tk.StringVar(value=DEFAULT_SAVE_PATH)
        self.mode            = tk.StringVar(value="video")
        self.video_fmt       = tk.StringVar(value="mp4")
        self.audio_fmt       = tk.StringVar(value="mp3")
        self.convert_src_fmt = tk.StringVar(value="mkv")
        self.convert_dst_fmt = tk.StringVar(value="mp4")
        self.quality         = tk.StringVar(value="best")
        self.cookie_file     = tk.StringVar(value="")
        self.browser_var     = tk.StringVar(value="none")
        self.save_log        = tk.BooleanVar(value=False)
        self.log_file_path   = tk.StringVar(value=DEFAULT_SAVE_PATH)

        # Non-UI state  ------------------------------------------------------
        self.log_queue:      queue.Queue        = queue.Queue()
        self.convert_files:  list[str]          = []
        self._log_buffer:    list[str]          = []
        self._downloader:    Downloader | None  = None
        self._converter:     Converter | None   = None

        # Build UI  ----------------------------------------------------------
        self._apply_style()
        self._build_ui()
        self._poll_log()

    # ── i18n shortcuts ────────────────────────────────────────────────────────

    def t(self, key: str, **kwargs) -> str:
        return self.tr.t(key, **kwargs)

    def _sync_title(self) -> None:
        self.title(f"{self.t('app_title')}  ·  v{APP_VERSION}")

    def _on_language_change(self, *_args) -> None:
        code = LANG_CODE_FROM_DISPLAY.get(self.lang_var.get(), "en")
        self.tr.set_language(code)
        self._sync_title()
        self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        """Tear down the UI and rebuild it in the active language."""
        # Remember log contents and currently-queued convert files.
        try:
            log_text = self.log_box.get("1.0", "end-1c")
        except Exception:
            log_text = ""

        # Wipe everything except the root.
        for child in self.winfo_children():
            child.destroy()

        self._build_ui()

        # Restore log contents.
        if log_text:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", log_text)
            self.log_box.configure(state="disabled")

        # Re-insert any queued convert files (translated status).
        for fp in list(self.convert_files):
            try:
                sz = format_filesize(os.path.getsize(fp))
            except OSError:
                sz = "-"
            self.cv_tree.insert(
                "", "end", iid=fp,
                values=(os.path.basename(fp), sz, self.t("tree_pending")),
            )

    # ── 4b · ttk styles ───────────────────────────────────────────────────────

    def _apply_style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")

        bg, surf, surf2, brd = DARK["bg"], DARK["surface"], DARK["surface2"], DARK["border"]
        text, dim, acc, acc2 = DARK["text"], DARK["text_dim"], DARK["accent"], DARK["accent2"]
        dng, prog            = DARK["danger"], DARK["progress"]

        s.configure("TFrame",      background=bg)
        s.configure("Surf.TFrame", background=surf)

        s.configure("TLabel",         background=bg,   foreground=text, font=("Segoe UI", 10))
        s.configure("Surf.TLabel",    background=surf, foreground=text, font=("Segoe UI", 10))
        s.configure("Dim.TLabel",     background=bg,   foreground=dim,  font=("Segoe UI", 9))
        s.configure("Acc.TLabel",     background=surf, foreground=acc,  font=("Segoe UI", 10, "bold"))

        s.configure("TButton",
                    background=surf2, foreground=text,
                    font=("Segoe UI", 10), relief="flat",
                    borderwidth=0, padding=(12, 6))
        s.map("TButton", background=[("active", brd)])

        s.configure("Accent.TButton",
                    background=acc, foreground="#ffffff",
                    font=("Segoe UI", 10, "bold"),
                    relief="flat", padding=(16, 8))
        s.map("Accent.TButton", background=[("active", "#79c0ff")])

        s.configure("Green.TButton",
                    background=acc2, foreground="#ffffff",
                    font=("Segoe UI", 10, "bold"),
                    relief="flat", padding=(16, 8))
        s.map("Green.TButton", background=[("active", "#56d364")])

        s.configure("Danger.TButton",
                    background=dng, foreground="#ffffff",
                    font=("Segoe UI", 10), relief="flat",
                    padding=(10, 6))
        s.map("Danger.TButton", background=[("active", "#ff7b72")])

        s.configure("TCombobox",
                    fieldbackground=DARK["input_bg"], background=surf2,
                    foreground=text, selectbackground=surf2,
                    padding=(4, 4))
        s.map("TCombobox",
              fieldbackground=[("readonly", DARK["input_bg"])],
              foreground=[("readonly", text)])

        s.configure("Horizontal.TProgressbar",
                    troughcolor=surf2, background=prog,
                    borderwidth=0, lightcolor=prog, darkcolor=prog)

        s.configure("TNotebook",     background=bg, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab", background=surf2, foreground=dim,
                    padding=(18, 9), font=("Segoe UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", surf)],
              foreground=[("selected", acc)])

        s.configure("Treeview",
                    background=surf, fieldbackground=surf,
                    foreground=text, rowheight=30,
                    font=("Segoe UI", 9))
        s.map("Treeview",
              background=[("selected", brd)],
              foreground=[("selected", acc)])
        s.configure("Treeview.Heading",
                    background=surf2, foreground=dim,
                    font=("Segoe UI", 9, "bold"))

    # ── 4c · Top-level layout ─────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()
        tk.Frame(self, bg=DARK["border"], height=1).pack(fill="x")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        tab_dl = tk.Frame(nb, bg=DARK["bg"])
        tab_cv = tk.Frame(nb, bg=DARK["bg"])
        nb.add(tab_dl, text=self.t("tab_download"))
        nb.add(tab_cv, text=self.t("tab_convert"))

        self._build_download_tab(tab_dl)
        self._build_convert_tab(tab_cv)

    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=DARK["surface"], height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        inner = tk.Frame(hdr, bg=DARK["surface"])
        inner.pack(fill="both", expand=True, padx=24)

        # Left: title + version
        left = tk.Frame(inner, bg=DARK["surface"])
        left.pack(side="left", fill="y")
        tk.Label(left, text=f"⬇  {self.t('app_title')}",
                 bg=DARK["surface"], fg=DARK["accent"],
                 font=("Segoe UI", 17, "bold")).pack(side="left", pady=16)
        tk.Label(left, text=f"v{APP_VERSION}",
                 bg=DARK["surface"], fg=DARK["text_muted"],
                 font=("Segoe UI", 9)).pack(side="left", padx=12, pady=22)

        # Right: language selector + subtitle
        right = tk.Frame(inner, bg=DARK["surface"])
        right.pack(side="right", fill="y")

        tk.Label(right, text=self.t("language") + ":",
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 6), pady=22)

        lang_combo = ttk.Combobox(
            right, textvariable=self.lang_var,
            values=list(LANG_DISPLAY.values()),
            state="readonly", width=12,
        )
        lang_combo.pack(side="left", pady=22)
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        tk.Label(right, text="  " + self.t("app_subtitle"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9)).pack(side="left", pady=22, padx=(12, 0))

    # ── 4d · Download tab ─────────────────────────────────────────────────────

    def _build_download_tab(self, parent: tk.Frame) -> None:
        # Outer Canvas + Scrollbar so the tab content always scrolls.
        outer = tk.Frame(parent, bg=DARK["bg"])
        outer.pack(fill="both", expand=True)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer, bg=DARK["bg"], highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        vbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        vbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=vbar.set)

        wrap = tk.Frame(canvas, bg=DARK["bg"])
        wrap_id = canvas.create_window((0, 0), window=wrap, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(wrap_id, width=e.width))
        wrap.bind("<Configure>",
                  lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _on_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        for widget in (canvas, wrap):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>",   _on_mousewheel)
            widget.bind("<Button-5>",   _on_mousewheel)

        inner = tk.Frame(wrap, bg=DARK["bg"])
        inner.pack(fill="both", expand=True, padx=22, pady=18)

        # Cards
        self._section(inner, self.t("sec_mode"),   self._mode_content)
        self._section(inner, self.t("sec_format"), self._format_content)
        self._section(inner, self.t("sec_urls"),   self._url_content)
        self._section(inner, self.t("sec_save"),   self._savepath_content)
        self._section(inner, self.t("sec_cookie"), self._cookie_content)
        self._section(inner, self.t("sec_log"),    self._log_settings_content)

        # Action buttons
        btn_row = tk.Frame(inner, bg=DARK["bg"])
        btn_row.pack(fill="x", pady=(6, 2))
        ttk.Button(btn_row, text=self.t("btn_start_download"),
                   style="Accent.TButton", command=self._start_download
                   ).pack(side="left")
        ttk.Button(btn_row, text=self.t("btn_stop"),
                   style="Danger.TButton", command=self._stop_jobs
                   ).pack(side="left", padx=(10, 0))

        # Progress
        self.dl_status_lbl = tk.Label(inner, text=self.t("status_ready_dl"),
                                       bg=DARK["bg"], fg=DARK["text_dim"],
                                       font=("Segoe UI", 9))
        self.dl_status_lbl.pack(anchor="w", pady=(8, 0))

        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(inner, variable=self.progress_var,
                        style="Horizontal.TProgressbar", maximum=100
                        ).pack(fill="x", pady=(2, 8))

        # Log area
        log_hdr = tk.Frame(inner, bg=DARK["bg"])
        log_hdr.pack(fill="x")
        tk.Label(log_hdr, text=self.t("log_title"),
                 bg=DARK["bg"], fg=DARK["accent"],
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(log_hdr, text=self.t("btn_clear"),
                   style="TButton", command=self._clear_log
                   ).pack(side="right")
        ttk.Button(log_hdr, text=self.t("btn_save_log_now"),
                   style="TButton", command=self._save_log_now
                   ).pack(side="right", padx=(0, 6))

        self.log_box = scrolledtext.ScrolledText(
            inner, height=8,
            bg=DARK["surface"], fg=DARK["text_dim"],
            insertbackground=DARK["accent"],
            font=("Consolas", 9), relief="flat", bd=0,
            state="disabled", selectbackground=DARK["border"],
        )
        self.log_box.pack(fill="x", pady=(4, 18))
        self.log_box.bind("<MouseWheel>", _on_mousewheel)
        self.log_box.bind("<Button-4>",   _on_mousewheel)
        self.log_box.bind("<Button-5>",   _on_mousewheel)

        self.log_box.tag_config("ok",   foreground=DARK["accent2"])
        self.log_box.tag_config("err",  foreground=DARK["danger"])
        self.log_box.tag_config("warn", foreground=DARK["warn"])
        self.log_box.tag_config("info", foreground=DARK["accent"])

    # ── 4e · Convert tab ──────────────────────────────────────────────────────

    def _build_convert_tab(self, parent: tk.Frame) -> None:
        wrap = tk.Frame(parent, bg=DARK["bg"])
        wrap.pack(fill="both", expand=True, padx=22, pady=18)

        # Format selection
        fmt_card = self._make_card(wrap, self.t("cv_format"))
        row_f = tk.Frame(fmt_card, bg=DARK["surface"])
        row_f.pack(fill="x", padx=14, pady=(0, 10))

        tk.Label(row_f, text=self.t("cv_from"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(row_f, textvariable=self.convert_src_fmt,
                     values=VIDEO_FORMATS + AUDIO_FORMATS,
                     state="readonly", width=8).pack(side="left", padx=(6, 0))

        tk.Label(row_f, text=self.t("cv_to"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(row_f, textvariable=self.convert_dst_fmt,
                     values=VIDEO_FORMATS + AUDIO_FORMATS,
                     state="readonly", width=8).pack(side="left", padx=(6, 0))

        # File list
        fl_card = self._make_card(wrap, self.t("cv_file_list"), expand=True)

        fl_hdr = tk.Frame(fl_card, bg=DARK["surface"])
        fl_hdr.pack(fill="x", padx=14, pady=(0, 4))
        ttk.Button(fl_hdr, text=self.t("btn_add_files"),
                   style="TButton", command=self._add_convert_files
                   ).pack(side="left")
        ttk.Button(fl_hdr, text=self.t("btn_add_folder"),
                   style="TButton", command=self._add_convert_folder
                   ).pack(side="left", padx=(6, 0))
        ttk.Button(fl_hdr, text=self.t("btn_remove_selected"),
                   style="Danger.TButton", command=self._remove_convert_file
                   ).pack(side="right")

        cols = ("file", "size", "status")
        self.cv_tree = ttk.Treeview(fl_card, columns=cols, show="headings", height=8)
        self.cv_tree.heading("file",   text=self.t("col_filename"))
        self.cv_tree.heading("size",   text=self.t("col_size"))
        self.cv_tree.heading("status", text=self.t("col_status"))
        self.cv_tree.column("file",   width=440)
        self.cv_tree.column("size",   width=110, anchor="center")
        self.cv_tree.column("status", width=160, anchor="center")
        self.cv_tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # Output location
        sp_card = self._make_card(wrap, self.t("cv_output"))
        row_sp = tk.Frame(sp_card, bg=DARK["surface"])
        row_sp.pack(fill="x", padx=14, pady=(0, 10))
        tk.Entry(row_sp, textvariable=self.cv_save_path,
                 bg=DARK["input_bg"], fg=DARK["text"],
                 insertbackground=DARK["accent"],
                 font=("Segoe UI", 10), relief="flat", bd=4
                 ).pack(side="left", fill="x", expand=True)
        ttk.Button(row_sp, text=self.t("btn_browse"),
                   style="TButton",
                   command=lambda: self._browse_save(self.cv_save_path)
                   ).pack(side="left", padx=(8, 0))

        # Action buttons
        btn_row = tk.Frame(wrap, bg=DARK["bg"])
        btn_row.pack(fill="x", pady=(4, 2))
        ttk.Button(btn_row, text=self.t("btn_start_convert"),
                   style="Green.TButton", command=self._start_convert
                   ).pack(side="left")
        ttk.Button(btn_row, text=self.t("btn_stop"),
                   style="Danger.TButton", command=self._stop_jobs
                   ).pack(side="left", padx=(10, 0))

        # Progress
        self.cv_status_lbl = tk.Label(wrap, text=self.t("status_ready_cv"),
                                       bg=DARK["bg"], fg=DARK["text_dim"],
                                       font=("Segoe UI", 9))
        self.cv_status_lbl.pack(anchor="w", pady=(8, 0))

        self.cv_progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(wrap, variable=self.cv_progress_var,
                        style="Horizontal.TProgressbar", maximum=100
                        ).pack(fill="x", pady=(2, 8))

        tk.Label(wrap, text=self.t("cv_ffmpeg_notice"),
                 bg=DARK["bg"], fg=DARK["warn"],
                 font=("Segoe UI", 8), wraplength=900, justify="left"
                 ).pack(anchor="w")

    # ── 4f · Card / section helpers ───────────────────────────────────────────

    def _make_card(self, parent: tk.Frame, title: str, *, expand: bool = False) -> tk.Frame:
        card = tk.Frame(parent, bg=DARK["surface"],
                        highlightthickness=1, highlightbackground=DARK["border"])
        card.pack(fill="both" if expand else "x", expand=expand, pady=(0, 10))
        tk.Label(card, text=title,
                 bg=DARK["surface"], fg=DARK["accent"],
                 font=("Segoe UI", 10, "bold")
                 ).pack(anchor="w", padx=14, pady=(10, 4))
        return card

    def _section(self, parent: tk.Frame, title: str, fill_fn) -> None:
        card = self._make_card(parent, title)
        fill_fn(card)

    def _mode_content(self, card: tk.Frame) -> None:
        row = tk.Frame(card, bg=DARK["surface"])
        row.pack(fill="x", padx=14, pady=(0, 10))
        for val, key in (("video", "mode_video"), ("audio", "mode_audio")):
            tk.Radiobutton(
                row, text=self.t(key), variable=self.mode, value=val,
                bg=DARK["surface"], fg=DARK["text"],
                selectcolor=DARK["surface2"],
                activebackground=DARK["surface"],
                activeforeground=DARK["accent"],
                font=("Segoe UI", 10),
                command=self._on_mode_change,
            ).pack(side="left", padx=(0, 28))

    def _format_content(self, card: tk.Frame) -> None:
        row = tk.Frame(card, bg=DARK["surface"])
        row.pack(fill="x", padx=14, pady=(0, 10))

        self.video_fmt_row = tk.Frame(row, bg=DARK["surface"])
        self.video_fmt_row.pack(side="left")
        tk.Label(self.video_fmt_row, text=self.t("lbl_video_fmt"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(self.video_fmt_row, textvariable=self.video_fmt,
                     values=VIDEO_FORMATS, state="readonly", width=8
                     ).pack(side="left", padx=(6, 0))

        self.audio_fmt_row = tk.Frame(row, bg=DARK["surface"])
        tk.Label(self.audio_fmt_row, text=self.t("lbl_audio_fmt"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9)).pack(side="left")
        ttk.Combobox(self.audio_fmt_row, textvariable=self.audio_fmt,
                     values=AUDIO_FORMATS, state="readonly", width=8
                     ).pack(side="left", padx=(6, 0))

        tk.Label(row, text="  " + self.t("lbl_quality"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(18, 0))
        ttk.Combobox(row, textvariable=self.quality,
                     values=QUALITY_PRESETS, state="readonly", width=8
                     ).pack(side="left", padx=(6, 0))

        self._on_mode_change()

    def _url_content(self, card: tk.Frame) -> None:
        self.url_text = tk.Text(card, height=5,
                                bg=DARK["input_bg"], fg=DARK["text"],
                                insertbackground=DARK["accent"],
                                font=("Consolas", 10), relief="flat", bd=0,
                                wrap="none", selectbackground=DARK["border"])
        self.url_text.pack(fill="x", padx=14, pady=(0, 4))

        row = tk.Frame(card, bg=DARK["surface"])
        row.pack(fill="x", padx=14, pady=(0, 10))
        ttk.Button(row, text=self.t("btn_clear"),
                   style="TButton",
                   command=lambda: self.url_text.delete("1.0", "end")
                   ).pack(side="left", padx=(0, 6))
        ttk.Button(row, text=self.t("btn_paste"),
                   style="TButton", command=self._paste_url
                   ).pack(side="left")
        tk.Label(row, text=self.t("urls_caption"),
                 bg=DARK["surface"], fg=DARK["text_muted"],
                 font=("Segoe UI", 8)).pack(side="right")

    def _savepath_content(self, card: tk.Frame) -> None:
        row = tk.Frame(card, bg=DARK["surface"])
        row.pack(fill="x", padx=14, pady=(0, 10))
        tk.Entry(row, textvariable=self.save_path,
                 bg=DARK["input_bg"], fg=DARK["text"],
                 insertbackground=DARK["accent"],
                 font=("Segoe UI", 10), relief="flat", bd=4
                 ).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text=self.t("btn_browse"),
                   style="TButton",
                   command=lambda: self._browse_save(self.save_path)
                   ).pack(side="left", padx=(8, 0))

    def _cookie_content(self, card: tk.Frame) -> None:
        tk.Label(card, text=self.t("cookie_warning"),
                 bg=DARK["surface"], fg=DARK["warn"],
                 font=("Segoe UI", 8), wraplength=860, justify="left"
                 ).pack(anchor="w", padx=14, pady=(4, 8))

        row1 = tk.Frame(card, bg=DARK["surface"])
        row1.pack(fill="x", padx=14, pady=(0, 6))
        tk.Label(row1, text=self.t("cookie_m1"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Combobox(row1, textvariable=self.browser_var,
                     values=BROWSERS, state="readonly", width=12
                     ).pack(side="left", padx=(8, 0))
        tk.Label(row1, text="  " + self.t("cookie_m1_hint"),
                 bg=DARK["surface"], fg=DARK["text_muted"],
                 font=("Segoe UI", 8)).pack(side="left")

        row2 = tk.Frame(card, bg=DARK["surface"])
        row2.pack(fill="x", padx=14, pady=(0, 10))
        tk.Label(row2, text=self.t("cookie_m2"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Entry(row2, textvariable=self.cookie_file,
                 bg=DARK["input_bg"], fg=DARK["text"],
                 insertbackground=DARK["accent"],
                 font=("Segoe UI", 9), relief="flat", bd=4, width=36
                 ).pack(side="left", padx=(8, 0))
        ttk.Button(row2, text=self.t("btn_browse"),
                   style="TButton", command=self._browse_cookie_file
                   ).pack(side="left", padx=(6, 0))
        ttk.Button(row2, text=self.t("btn_clear"),
                   style="TButton",
                   command=lambda: self.cookie_file.set("")
                   ).pack(side="left", padx=(4, 0))

        tk.Label(card, text=self.t("cookie_export_hint"),
                 bg=DARK["surface"], fg=DARK["text_muted"],
                 font=("Segoe UI", 8), wraplength=860, justify="left"
                 ).pack(anchor="w", padx=14, pady=(0, 10))

    def _log_settings_content(self, card: tk.Frame) -> None:
        row_toggle = tk.Frame(card, bg=DARK["surface"])
        row_toggle.pack(fill="x", padx=14, pady=(6, 4))

        tk.Checkbutton(
            row_toggle, text=self.t("log_auto_toggle"),
            variable=self.save_log,
            bg=DARK["surface"], fg=DARK["text"],
            selectcolor=DARK["surface2"],
            activebackground=DARK["surface"],
            activeforeground=DARK["accent"],
            font=("Segoe UI", 10),
            command=self._on_save_log_toggle,
        ).pack(side="left")

        self._log_path_row = tk.Frame(card, bg=DARK["surface"])
        tk.Label(self._log_path_row, text=self.t("log_save_dir"),
                 bg=DARK["surface"], fg=DARK["text_dim"],
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(self._log_path_row, textvariable=self.log_file_path,
                 bg=DARK["input_bg"], fg=DARK["text"],
                 insertbackground=DARK["accent"],
                 font=("Segoe UI", 9), relief="flat", bd=4
                 ).pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Button(self._log_path_row, text=self.t("btn_browse"),
                   style="TButton",
                   command=lambda: self._browse_save(self.log_file_path)
                   ).pack(side="left", padx=(6, 0))

        self._log_fmt_label = tk.Label(
            card, text=self.t("log_fmt_note"),
            bg=DARK["surface"], fg=DARK["text_muted"],
            font=("Segoe UI", 8), wraplength=860, justify="left",
        )

        # Restore visibility based on current toggle state.
        if self.save_log.get():
            self._on_save_log_toggle()

    # ── 4g · Small UI helpers ─────────────────────────────────────────────────

    def _on_mode_change(self) -> None:
        if self.mode.get() == "video":
            self.video_fmt_row.pack(side="left")
            self.audio_fmt_row.pack_forget()
        else:
            self.video_fmt_row.pack_forget()
            self.audio_fmt_row.pack(side="left")

    def _browse_save(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory(
            initialdir=var.get(),
            title=self.t("dlg_select_save"),
        )
        if path:
            var.set(path)

    def _paste_url(self) -> None:
        try:
            txt = self.clipboard_get()
            if txt.strip():
                self.url_text.insert("end", txt.strip() + "\n")
        except Exception:
            pass  # empty clipboard or platform error

    def _browse_cookie_file(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("dlg_select_cookie"),
            filetypes=[(self.t("ft_cookie"), "*.txt"), (self.t("ft_all"), "*.*")],
        )
        if path:
            self.cookie_file.set(path)

    def _on_save_log_toggle(self) -> None:
        if self.save_log.get():
            self._log_path_row.pack(fill="x", padx=14, pady=(0, 4))
            self._log_fmt_label.pack(anchor="w", padx=14, pady=(0, 10))
        else:
            self._log_path_row.pack_forget()
            self._log_fmt_label.pack_forget()

    # ── 4h · Log handling ─────────────────────────────────────────────────────

    def _log_event(self, level: str, key: str, **fmt) -> None:
        """Core-side callback: enqueue a translated, formatted log line."""
        self.log_queue.put((self.t(key, **fmt), level))

    def _clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _poll_log(self) -> None:
        try:
            while True:
                msg, tag = self.log_queue.get_nowait()
                ts   = datetime.now().strftime("%H:%M:%S")
                line = f"[{ts}] {msg}\n"
                self.log_box.configure(state="normal")
                self.log_box.insert("end", line, tag or "")
                self.log_box.see("end")
                self.log_box.configure(state="disabled")
                self._log_buffer.append(line)
        except queue.Empty:
            pass
        self.after(100, self._poll_log)

    def _flush_log_to_file(self) -> None:
        if not self.save_log.get() or not self._log_buffer:
            return

        save_dir = self.log_file_path.get().strip()
        if not os.path.isdir(save_dir):
            self._log_event("warn", "log_save_failed_dir", path=save_dir)
            return

        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"download_log_{ts}.txt"
        path = os.path.join(save_dir, name)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write(f"{self.t('log_file_header')}\n")
                f.write(f"{self.t('log_file_generated', ts=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n")
                f.write("=" * 60 + "\n\n")
                f.writelines(self._log_buffer)
                f.write("\n" + "=" * 60 + "\n")
                f.write(f"{self.t('log_file_end', n=len(self._log_buffer))}\n")
            self._log_event("ok", "log_saved", name=name)
        except OSError as e:
            self._log_event("warn", "log_save_failed", err=str(e))
        finally:
            self._log_buffer.clear()

    def _save_log_now(self) -> None:
        if not self._log_buffer:
            messagebox.showinfo(self.t("msg_log_empty_title"),
                                self.t("msg_log_empty_body"))
            return
        orig = self.save_log.get()
        self.save_log.set(True)
        self._flush_log_to_file()
        self.save_log.set(orig)

    # ── 4i · Download orchestration ───────────────────────────────────────────

    def _get_urls(self) -> list[str]:
        raw = self.url_text.get("1.0", "end").strip()
        return [u.strip() for u in raw.splitlines() if u.strip()]

    def _stop_jobs(self) -> None:
        if self._downloader:
            self._downloader.stop()
        if self._converter:
            self._converter.stop()
        self._log_event("warn", "log_stopping")

    def _start_download(self) -> None:
        urls = self._get_urls()
        if not urls:
            messagebox.showwarning(self.t("msg_no_url_title"),
                                   self.t("msg_no_url_body"))
            return

        save = self.save_path.get()
        if not os.path.isdir(save):
            messagebox.showerror(self.t("msg_bad_path_title"),
                                 self.t("msg_bad_path_body", path=save))
            return

        cookie_file = self.cookie_file.get().strip() or None
        browser = self.browser_var.get() if self.browser_var.get() != "none" else None

        opts = DownloadOptions(
            save_path   = save,
            mode        = self.mode.get(),
            video_fmt   = self.video_fmt.get(),
            audio_fmt   = self.audio_fmt.get(),
            quality     = self.quality.get(),
            cookie_file = cookie_file,
            browser     = browser,
        )

        def _progress(pct: float, speed: str, eta: str) -> None:
            self.after(0, lambda: self.progress_var.set(pct))
            self.after(0, lambda: self.dl_status_lbl.config(
                text=self.t("status_progress",
                            pct=f"{pct:.1f}", speed=speed, eta=eta)
            ))

        def _item_start(i: int, t: int, url: str) -> None:
            display = url if len(url) <= 70 else url[:67] + "..."
            self.after(0, lambda: self.dl_status_lbl.config(
                text=self.t("status_downloading", n=i, t=t, url=display)
            ))

        self._downloader = Downloader(
            opts,
            log_cb        = self._log_event,
            progress_cb   = _progress,
            item_start_cb = _item_start,
        )
        total = len(urls)
        self.progress_var.set(0)

        def _worker() -> None:
            self._downloader.download_batch(urls)
            self.after(0, lambda: self.dl_status_lbl.config(
                text=self.t("status_all_done_dl", t=total)
            ))
            self.after(200, self._flush_log_to_file)

        threading.Thread(target=_worker, daemon=True).start()

    # ── 4j · Convert orchestration ────────────────────────────────────────────

    def _add_convert_files(self) -> None:
        exts = VIDEO_FORMATS + AUDIO_FORMATS
        ftypes = [(self.t("ft_media"), " ".join(f"*.{e}" for e in exts)),
                  (self.t("ft_all"), "*.*")]
        for f in filedialog.askopenfilenames(
                title=self.t("dlg_select_files"), filetypes=ftypes):
            if f in self.convert_files:
                continue
            self.convert_files.append(f)
            sz = format_filesize(os.path.getsize(f))
            self.cv_tree.insert(
                "", "end", iid=f,
                values=(os.path.basename(f), sz, self.t("tree_pending")),
            )

    def _add_convert_folder(self) -> None:
        folder = filedialog.askdirectory(title=self.t("dlg_select_folder"))
        if not folder:
            return
        exts = set(VIDEO_FORMATS + AUDIO_FORMATS)
        for fn in sorted(os.listdir(folder)):
            ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
            if ext not in exts:
                continue
            fp = os.path.join(folder, fn)
            if fp in self.convert_files:
                continue
            self.convert_files.append(fp)
            sz = format_filesize(os.path.getsize(fp))
            self.cv_tree.insert(
                "", "end", iid=fp,
                values=(fn, sz, self.t("tree_pending")),
            )

    def _remove_convert_file(self) -> None:
        for iid in self.cv_tree.selection():
            self.cv_tree.delete(iid)
            if iid in self.convert_files:
                self.convert_files.remove(iid)

    def _start_convert(self) -> None:
        if not self.convert_files:
            messagebox.showwarning(self.t("msg_no_files_title"),
                                   self.t("msg_no_files_body"))
            return

        if self.convert_src_fmt.get() == self.convert_dst_fmt.get():
            messagebox.showwarning(self.t("msg_same_fmt_title"),
                                   self.t("msg_same_fmt_body"))
            return

        save = self.cv_save_path.get()
        if not os.path.isdir(save):
            messagebox.showerror(self.t("msg_bad_path_title"),
                                 self.t("msg_bad_path_body", path=save))
            return

        dst_fmt = self.convert_dst_fmt.get()
        files = list(self.convert_files)
        total = len(files)
        self.cv_progress_var.set(0)

        status_keys = {
            "pending":    "tree_pending",
            "converting": "tree_converting",
            "done":       "tree_done",
            "error":      "tree_error",
            "no_ffmpeg":  "tree_need_ffmpeg",
        }

        def _on_job_update(job):
            key = status_keys.get(job.status, "tree_pending")
            self.after(0, lambda: self._update_tree_status(
                job.src_path, os.path.basename(job.src_path), self.t(key)))

        self._converter = Converter(
            save_path     = save,
            dst_fmt       = dst_fmt,
            log_cb        = self._log_event,
            job_update_cb = _on_job_update,
        )

        def _worker():
            for i, fp in enumerate(files, start=1):
                self.after(0, lambda f=fp, n=i: self.cv_status_lbl.config(
                    text=self.t("status_converting", n=n, t=total,
                                file=os.path.basename(f))
                ))
                self.after(0, lambda v=i / total * 100: self.cv_progress_var.set(v))
                # Convert one file at a time so we get per-item progress updates.
                self._converter.convert_batch([fp])
                if self._converter._stop:  # type: ignore[attr-defined]
                    break
            self.after(0, lambda: self.cv_status_lbl.config(
                text=self.t("status_all_done_cv", t=total)
            ))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_tree_status(self, iid: str, fn: str, status: str) -> None:
        try:
            cur = self.cv_tree.item(iid).get("values", [])
            size_val = cur[1] if len(cur) > 1 else ""
            self.cv_tree.item(iid, values=(fn, size_val, status))
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  SECTION 5 ── Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    app = MultimediaDownloader()
    app.mainloop()


if __name__ == "__main__":
    main()
