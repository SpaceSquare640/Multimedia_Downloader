"""Main Textual application — composes the Download/Convert/Log tabs."""

from __future__ import annotations

import argparse
import os
import sys

# Make the bundled engine importable no matter where this is invoked from,
# same defensive shim as cli.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, TabbedContent, TabPane

import i18n

from .convert_tab import ConvertTab
from .download_tab import DownloadTab
from .log_tab import LogTab

_STYLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.tcss")


class MultimediaDownloaderApp(App):
    """Terminal UI over the same ``engine/`` package the desktop and web apps use."""

    CSS_PATH = _STYLE_PATH
    TITLE = "Multimedia Downloader"
    BINDINGS = [
        ("d", "toggle_dark", "Dark mode"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, tr: "i18n.Translator") -> None:
        super().__init__()
        self.tr = tr

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane(self.tr.t("tab_download"), id="tab-download"):
                yield DownloadTab(self.tr)
            with TabPane(self.tr.t("tab_convert"), id="tab-convert"):
                yield ConvertTab(self.tr)
            with TabPane(self.tr.t("tab_log"), id="tab-log"):
                yield LogTab(self.tr)
        yield Footer()

    def log_line(self, level: str, key: str, **fmt) -> None:
        """Called from any tab (via ``call_from_thread`` if off the UI thread) to
        route an engine log event to the Log tab, translated to the active language."""
        self.query_one(LogTab).append_entry(level, self.tr.t(key, **fmt))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mmdl-tui",
        description="Multimedia Downloader — interactive terminal UI.",
    )
    p.add_argument("--lang", default="en", help="interface language: en / zh_tw / zh_cn")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    tr = i18n.Translator(args.lang)
    MultimediaDownloaderApp(tr).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
