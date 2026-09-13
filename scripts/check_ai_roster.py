#!/usr/bin/env python3
"""
Report whether the AI assistant's default model ids are still live.

`ai/models.resolve_roster()` already keeps the assistant working when a model
is retired, by substituting a live free one. That makes retirement survivable,
not invisible: every user then sees a substitution warning, and the substitute
is whatever happens to be available rather than one that was chosen for the
role. The free tier churns roughly every couple of months -- three rounds are
on record -- so this is run on a schedule to surface the drift while it is
still a maintenance task rather than a user-facing surprise.

Exit codes:
    0  every default is live
    1  at least one default has been retired (details on stdout)
    2  the catalogue could not be read -- inconclusive, not a failure of the roster

Loads ai/models.py directly rather than importing the `ai` package, whose
__init__ pulls in the engine and therefore yt-dlp. This way the workflow needs
no dependencies at all.
"""

from __future__ import annotations

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_models_module():
    path = os.path.join(ROOT, "ai", "models.py")
    spec = importlib.util.spec_from_file_location("_mmdl_ai_models", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # @dataclass resolves annotations through sys.modules[cls.__module__], so
    # the module has to be registered before it is executed, not after.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    models = _load_models_module()
    roster = models.resolve_roster(use_cache=False)

    if not roster.verified:
        print("Could not read the OpenRouter catalogue — result is inconclusive.")
        for note in roster.notes:
            print(f"  {note}")
        return 2

    defaults = {m.role: m for m in models.ROSTER}
    retired = [role for role, want in defaults.items()
               if roster.get(role).slug != want.slug]

    for role, want in defaults.items():
        live = roster.get(role)
        if role in retired:
            print(f"RETIRED  {role:<11} {want.slug}")
            print(f"         would now fall back to {live.slug}")
        else:
            print(f"live     {role:<11} {want.slug}")

    if not retired:
        print("\nAll four defaults are still live — nothing to do.")
        return 0

    print(f"\n{len(retired)} of {len(defaults)} defaults have been retired: "
          f"{', '.join(retired)}.")
    print("Update the constants in ai/models.py to currently live ids; the list "
          "above shows what resolve_roster() picks in the meantime.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
