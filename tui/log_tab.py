"""Log tab — live run log with search/level filtering, export, and clear."""

from __future__ import annotations

from datetime import datetime

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Select

from .widgets import ConfirmDialog

_LEVEL_COLOR = {
    "ok": "green",
    "warn": "yellow",
    "err": "red",
    "info": "grey70",
}


class LogTab(Vertical):
    """Owns the log entry buffer; the desktop/web frontends keep an equivalent list."""

    def __init__(self, tr) -> None:
        super().__init__()
        self.tr = tr
        self._entries: list[tuple[str, str, str]] = []  # (ts, level, text)

    def compose(self) -> ComposeResult:
        tr = self.tr
        with Horizontal(classes="toolbar"):
            yield Input(placeholder=tr.t("log_search"), id="search")
            yield Select(
                [
                    (tr.t("log_level_all"), "all"),
                    ("info", "info"),
                    ("ok", "ok"),
                    ("warn", "warn"),
                    ("err", "err"),
                ],
                value="all",
                id="level",
                allow_blank=False,
            )
            yield Button(tr.t("log_autoscroll"), id="autoscroll", variant="primary")
            yield Button(tr.t("log_export"), id="export")
            yield Button(tr.t("btn_clear"), id="clear")
        yield RichLog(id="console", wrap=True, markup=True)

    def append_entry(self, level: str, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._entries.append((ts, level, text))
        if self._passes_filter(level, text):
            self._write_line(ts, level, text)

    def _passes_filter(self, level: str, text: str) -> bool:
        level_filter = self.query_one("#level", Select).value
        if level_filter != "all" and level != level_filter:
            return False
        search = self.query_one("#search", Input).value.strip().lower()
        if search and search not in text.lower():
            return False
        return True

    def _write_line(self, ts: str, level: str, text: str) -> None:
        # `text` comes from arbitrary engine/yt-dlp/ffmpeg output (URLs, error
        # strings, filenames) and routinely contains literal "[...]" (e.g.
        # yt-dlp's "[youtube] ..." prefix, ffmpeg's "[mp4 @ 0xADDR]"). Building
        # a Text object directly -- instead of an f-string handed to a
        # markup=True RichLog -- means that content is never parsed as Rich
        # markup, so it can't be silently swallowed or raise MarkupError.
        color = _LEVEL_COLOR.get(level, "white")
        console = self.query_one("#console", RichLog)
        line = Text.assemble((f"{ts} ", "grey50"), (text, color))
        console.write(line)
        if self.query_one("#autoscroll", Button).variant == "primary":
            console.scroll_end(animate=False)

    def _refilter(self) -> None:
        console = self.query_one("#console", RichLog)
        console.clear()
        for ts, level, text in self._entries:
            if self._passes_filter(level, text):
                self._write_line(ts, level, text)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self._refilter()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "level":
            self._refilter()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "autoscroll":
            btn = event.button
            btn.variant = "default" if btn.variant == "primary" else "primary"
        elif event.button.id == "export":
            self._export()
        elif event.button.id == "clear":
            self._confirm_clear()

    def _confirm_clear(self) -> None:
        if not self._entries:
            return

        def handle(confirmed: bool | None) -> None:
            if confirmed:
                self._entries.clear()
                self.query_one("#console", RichLog).clear()

        self.app.push_screen(
            ConfirmDialog(
                self.tr.t("log_clear_confirm_title"),
                self.tr.t("log_clear_confirm_body"),
                self.tr.t("btn_clear"),
                self.tr.t("btn_cancel"),
            ),
            handle,
        )

    def _export(self) -> None:
        if not self._entries:
            self.app.notify(self.tr.t("msg_log_empty_body"), severity="warning")
            return
        name = f"mmdl_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        lines = [
            self.tr.t("log_file_header"),
            self.tr.t("log_file_generated", ts=datetime.now().isoformat(timespec="seconds")),
            "",
        ]
        lines += [f"[{ts}] [{level.upper():4}] {text}" for ts, level, text in self._entries]
        lines.append("")
        lines.append(self.tr.t("log_file_end", n=len(self._entries)))
        try:
            with open(name, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            self.app.notify(self.tr.t("log_saved", name=name))
        except OSError as e:
            self.app.notify(self.tr.t("log_save_failed", err=str(e)), severity="error")
