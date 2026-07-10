"""
Internationalization (i18n) for Multimedia Downloader V4.0.

Reads translations from JSON locale files in ``../locales`` instead of the
hard-coded Python dict used in V3.0 ``i18n.py``. Adding a language now means
dropping a new ``<code>.json`` file into ``locales/`` — no code change.

The :class:`Translator` API and fallback semantics match V3.0 exactly:
requested language → English → raw key. This same JSON is consumed by the
frontend TypeScript loader (``frontend/src/i18n``), so both sides stay in sync.

Usage
-----
    from i18n import Translator
    tr = Translator("zh_tw")
    tr.t("app_title")
    tr.t("log_item_done", i=1, t=3)
"""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache

DEFAULT_LANG = "en"


def _locales_dir() -> str:
    """
    Resolve the locales directory in both source and packaged (frozen) runs.

    * Source:   locales/ sits next to this package (…/Version4.0/locales).
    * Frozen:   PyInstaller unpacks bundled data under ``sys._MEIPASS`` (onefile)
                or beside the executable (onedir); we add ``locales`` there via
                the build's ``--add-data`` / spec ``datas`` entry.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        cand = os.path.join(base, "locales")
        if os.path.isdir(cand):
            return cand
    if getattr(sys, "frozen", False):
        cand = os.path.join(os.path.dirname(sys.executable), "locales")
        if os.path.isdir(cand):
            return cand
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")


_LOCALES_DIR = _locales_dir()


@lru_cache(maxsize=None)
def _load_all() -> dict[str, dict[str, str]]:
    """Load every ``locales/*.json`` once. Returns ``{lang: {key: value}}``."""
    data: dict[str, dict[str, str]] = {}
    if not os.path.isdir(_LOCALES_DIR):
        return data
    for name in os.listdir(_LOCALES_DIR):
        if not name.endswith(".json"):
            continue
        path = os.path.join(_LOCALES_DIR, name)
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        lang = doc.get("_meta", {}).get("lang") or os.path.splitext(name)[0]
        data[lang] = {k: v for k, v in doc.items() if k != "_meta"}
    return data


def available() -> dict[str, str]:
    """Return ``{lang_code: display_name}`` for every installed locale."""
    out: dict[str, str] = {}
    for name in sorted(os.listdir(_LOCALES_DIR)) if os.path.isdir(_LOCALES_DIR) else []:
        if not name.endswith(".json"):
            continue
        with open(os.path.join(_LOCALES_DIR, name), encoding="utf-8") as f:
            meta = json.load(f).get("_meta", {})
        code = meta.get("lang") or os.path.splitext(name)[0]
        out[code] = meta.get("name", code)
    return out


def reload() -> None:
    """Clear the cache so edited locale files are picked up (dev convenience)."""
    _load_all.cache_clear()


class Translator:
    """
    Lightweight runtime translator backed by JSON locale files.

    Falls back gracefully on missing keys: requested lang → English → raw key.
    ``t(key, **kwargs)`` applies ``str.format`` when kwargs are supplied; an
    unresolvable template returns the raw (unformatted) string rather than
    raising, so a stray missing arg never crashes the UI.
    """

    def __init__(self, lang: str = DEFAULT_LANG) -> None:
        strings = _load_all()
        self.lang = lang if lang in strings else DEFAULT_LANG

    def t(self, key: str, **kwargs) -> str:
        strings = _load_all()
        s = strings.get(self.lang, {}).get(key)
        if s is None:
            s = strings.get(DEFAULT_LANG, {}).get(key, key)
        if kwargs:
            try:
                return s.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                return s
        return s

    def set_language(self, lang: str) -> bool:
        """Set active language. Returns True if accepted, False otherwise."""
        if lang in _load_all():
            self.lang = lang
            return True
        return False

    @staticmethod
    def available() -> dict[str, str]:
        return available()
