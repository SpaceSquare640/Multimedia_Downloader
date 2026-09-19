#!/usr/bin/env python3
"""
Fail if the project's version number disagrees across the files that carry it.

The version lives in seven places. Bumping a release means editing all of them by
hand, and that has already gone wrong: `src-tauri/Cargo.toml` was left at 4.3.8
through the entire 4.3.9 release because nobody noticed the miss. A stale
Cargo.toml is what stamps the version into the built binary, so the installer
would have reported the wrong version to users.

Run it directly (`python scripts/check_version_consistency.py`) or let CI do it.
Exits 0 when every source agrees, 1 otherwise, printing what disagreed.

Deliberately stdlib-only and dependency-free so CI can run it before installing
anything.
"""

from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: A version we failed to find at all — distinct from finding a wrong one, since
#: the two mean different things (broken checker vs. missed bump).
MISSING = "<not found>"


def _read(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def _json_version(rel: str) -> str:
    return json.loads(_read(rel)).get("version") or MISSING


def _search(rel: str, pattern: str) -> str:
    m = re.search(pattern, _read(rel), re.MULTILINE)
    return m.group(1) if m else MISSING


def collect() -> dict[str, str]:
    """Map each source to the version it declares."""
    return {
        "package.json": _json_version("package.json"),
        "src-tauri/tauri.conf.json": _json_version("src-tauri/tauri.conf.json"),
        # [package] version — the first `version = "..."` in the file, which sits
        # above any [dependencies] section.
        "src-tauri/Cargo.toml": _search("src-tauri/Cargo.toml", r'^version\s*=\s*"([^"]+)"'),
        # The lockfile's entry for this crate; cargo rewrites it otherwise.
        "src-tauri/Cargo.lock": _search(
            "src-tauri/Cargo.lock",
            r'^name = "multimedia-downloader"\nversion = "([^"]+)"',
        ),
        # README title, e.g. `# Multimedia Downloader — V4.3.10`
        "README.md (title)": _search("README.md", r"^#\s+Multimedia Downloader\s+—\s+V(\S+)"),
        # Newest CHANGELOG entry, e.g. `### [4.3.10] — 2026-09-13`
        "CHANGELOG.md (newest entry)": _search("CHANGELOG.md", r"^###\s+\[([^\]]+)\]"),
        # Nothing reads this one, which is exactly why it rotted: it sat at
        # "4.0.0-dev" through every 4.x release. An unread constant with no
        # mechanism watching it is the same failure as Cargo.toml, minus the
        # symptom that eventually gave Cargo.toml away.
        "engine/__init__.py": _search("engine/__init__.py",
                                      r'^__version__\s*=\s*"([^"]+)"'),
    }


def main() -> int:
    versions = collect()
    distinct = set(versions.values())

    if len(distinct) == 1 and MISSING not in distinct:
        print(f"OK — all sources report version {distinct.pop()}")
        for source in versions:
            print(f"  {source}")
        return 0

    print("Version mismatch — these must all agree:", file=sys.stderr)
    width = max(len(s) for s in versions)
    # Report against the most common value, so the odd one out is obvious.
    expected = max(distinct, key=lambda v: list(versions.values()).count(v))
    for source, version in versions.items():
        mark = " " if version == expected else "<"
        print(f"  {mark} {source:<{width}}  {version}", file=sys.stderr)
    print(f"\nMost sources say {expected!r}; the lines marked '<' disagree.",
          file=sys.stderr)
    print("Bumping a release means updating every file listed above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
