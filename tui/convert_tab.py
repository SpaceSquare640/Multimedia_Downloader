"""Convert tab — local file format conversion, wired to engine.Converter."""

from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    Select,
    Static,
    TextArea,
)

from engine import AUDIO_FORMATS, VIDEO_FORMATS, Converter


class ConvertTab(VerticalScroll):
    """Composes the convert form; owns a single in-flight ``Converter``."""

    def __init__(self, tr) -> None:
        super().__init__()
        self.tr = tr
        self._converter: Converter | None = None
        self._files: list[str] = []
        # Kept in lockstep with ``_files`` (index i is always file i's row
        # widget) instead of re-derived from ``items.children`` at run time,
        # so a run started right after an add/remove can never see a stale
        # or not-yet-applied ListView mutation.
        self._item_widgets: list[Static] = []

    def compose(self) -> ComposeResult:
        tr = self.tr
        all_formats = list(VIDEO_FORMATS) + list(AUDIO_FORMATS)

        yield Label(tr.t("cv_file_list"), classes="section-title")
        yield TextArea(id="file-paths", soft_wrap=True)
        with Horizontal(classes="field-row"):
            yield Button(tr.t("btn_add_files"), id="add-file")
            yield Button(tr.t("btn_remove_selected"), id="remove-file")
        yield ListView(id="files-list")

        yield Label(tr.t("cv_format"), classes="section-title")
        with Horizontal(classes="field-row"):
            yield Select(((f, f) for f in all_formats), value=all_formats[0], id="dst-fmt", allow_blank=False)

        yield Label(tr.t("adv_options"), classes="section-title")
        yield Input(value="ffmpeg", id="ffmpeg-bin", classes="field-row")

        yield Label(tr.t("cv_output"), classes="section-title")
        yield Input(placeholder=".", id="save-path", classes="field-row")

        with Horizontal(classes="actions-row"):
            yield Button(tr.t("btn_start_convert"), id="start", variant="success")
            yield Button(tr.t("btn_stop"), id="stop", variant="error", disabled=True)

        yield Static("", id="status", classes="status-line")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-file":
            self._add_files()
        elif event.button.id == "remove-file":
            self._remove_selected()
        elif event.button.id == "start":
            self._start()
        elif event.button.id == "stop":
            self._stop()

    def _add_files(self) -> None:
        paths_area = self.query_one("#file-paths", TextArea)
        paths = [p.strip() for p in paths_area.text.splitlines() if p.strip()]
        if not paths:
            return
        items = self.query_one("#files-list", ListView)
        for path in paths:
            self._files.append(path)
            static = Static(path)
            self._item_widgets.append(static)
            items.append(ListItem(static))
        items.index = len(self._files) - 1  # highlight the last added row
        paths_area.text = ""

    def _remove_selected(self) -> None:
        items = self.query_one("#files-list", ListView)
        index = items.index
        if index is None or not (0 <= index < len(self._files)):
            return
        del self._files[index]
        del self._item_widgets[index]
        items.pop(index)

    def _start(self) -> None:
        if not self._files:
            self.app.notify(self.tr.t("msg_no_files_body"), severity="warning")
            return

        save_path = self.query_one("#save-path", Input).value.strip() or "."
        dst_fmt = self.query_one("#dst-fmt", Select).value
        ffmpeg_bin = self.query_one("#ffmpeg-bin", Input).value.strip() or "ffmpeg"

        pending = self.tr.t("tree_pending")
        for path, widget in zip(self._files, self._item_widgets):
            widget.update(f"{pending}  —  {path}")

        self.query_one("#start", Button).disabled = True
        self.query_one("#stop", Button).disabled = False
        self.query_one("#add-file", Button).disabled = True
        self.query_one("#remove-file", Button).disabled = True
        self._run_convert(list(self._files), save_path, dst_fmt, ffmpeg_bin)

    def _stop(self) -> None:
        converter = self._converter
        if converter is not None:
            converter.stop()
        self.query_one("#stop", Button).disabled = True

    @work(thread=True, exclusive=True)
    def _run_convert(self, files: list[str], save_path: str, dst_fmt: str, ffmpeg_bin: str) -> None:
        def log_cb(level: str, key: str, **fmt) -> None:
            self.app.call_from_thread(self.app.log_line, level, key, **fmt)

        # Map each ConvertJob to its row by object identity (in first-seen
        # order), not by re-looking-up job.src_path in `files` -- duplicate
        # paths would otherwise all resolve to the same (first) index.
        job_row: dict[int, int] = {}

        def job_update_cb(job) -> None:
            row = job_row.setdefault(id(job), len(job_row))
            self.app.call_from_thread(self._mark_item, row, job.status)

        converter = Converter(save_path=save_path, dst_fmt=dst_fmt, log_cb=log_cb,
                               job_update_cb=job_update_cb, ffmpeg_bin=ffmpeg_bin)
        self._converter = converter
        try:
            converter.convert_batch(files)
        finally:
            self._converter = None
            self.app.call_from_thread(self._finish)

    _STATUS_KEY = {
        "converting": "tree_converting",
        "done": "tree_done",
        "error": "tree_error",
        "no_ffmpeg": "tree_need_ffmpeg",
    }

    def _mark_item(self, index: int, status: str) -> None:
        label = self.tr.t(self._STATUS_KEY.get(status, "tree_pending"))
        if 0 <= index < len(self._item_widgets):
            self._item_widgets[index].update(f"{label}  —  {self._files[index]}")

    def _finish(self) -> None:
        self.query_one("#start", Button).disabled = False
        self.query_one("#stop", Button).disabled = True
        self.query_one("#add-file", Button).disabled = False
        self.query_one("#remove-file", Button).disabled = False
