"""
Import a test dependency, or fail loudly.

A skipped test reports as success. `unittest` prints the skip count next to an
`OK`, so a partial run looks exactly like a full one at a glance:

    Ran 133 tests in 12.004s
    OK (skipped=24)

Those 24 were the entire web backend suite -- the tests pinning the path
confinement -- silently absent because `flask` was not installed. "I ran the
tests" then means nothing, which is the same class of problem as the rest of
this release: a failure that stays quiet.

There is deliberately no opt-out. `tests/test_tui.py` already fails outright
when `textual` is missing (it imports `tui.app` at module scope), so hard
failure is the behaviour this suite already had everywhere except here; an
environment variable that restored skipping would half-apply, and would re-open
the exact hole this closes -- behind a flag that is easy to set once and forget.
Install `requirements-dev.txt`, which is what CI installs, or run a single
module directly (`python -m unittest tests.test_engine`) when you only want a
subset.
"""
import importlib


def require(module: str, install_with: str):
    """
    Return the imported ``module``, or raise ``ImportError`` naming the fix.

    The unittest loader turns the raised error into a reported failure, so the
    run cannot pass while the tests that need ``module`` are missing.
    """
    try:
        return importlib.import_module(module)
    except ImportError:
        raise ImportError(
            f"cannot import {module!r} -- something it needs is not installed, "
            "so the tests that depend on it cannot run, and skipping them "
            "would report as success. Install the missing dependency with "
            f"`pip install -r {install_with}`, or `pip install -r "
            "requirements-dev.txt`, which is what CI installs."
        ) from None
