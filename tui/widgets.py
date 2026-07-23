"""Small widgets shared across TUI tabs."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmDialog(ModalScreen[bool]):
    """A modal yes/no confirmation. Dismisses with True (confirm) or False (cancel)."""

    def __init__(self, title: str, body: str, confirm_label: str, cancel_label: str) -> None:
        super().__init__()
        self._title = title
        self._body = body
        self._confirm_label = confirm_label
        self._cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(self._title, classes="section-title")
            yield Label(self._body)
            with Horizontal(classes="actions-row"):
                yield Button(self._cancel_label, id="cancel")
                yield Button(self._confirm_label, id="confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(False)
