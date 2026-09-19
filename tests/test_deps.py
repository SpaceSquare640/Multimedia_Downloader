"""
Tests for tests/_deps.py — the guard that stops a partial run reporting OK.

This one is worth testing despite being test infrastructure: it decides whether
the suite tells the truth about what it ran.
"""
import unittest

import _deps
import _path  # noqa: F401


class RequireTests(unittest.TestCase):
    def test_present_module_is_returned(self):
        import json
        self.assertIs(_deps.require("json", "requirements-dev.txt"), json)

    def test_missing_module_raises_rather_than_returning_none(self):
        # Returning None is what the old code did, and it is what let the
        # caller fall back to a skip.
        with self.assertRaises(ImportError):
            _deps.require("a_module_that_does_not_exist", "requirements-web.txt")

    def test_error_names_the_install_command(self):
        # Someone hitting this needs to know the way out without reading source.
        with self.assertRaises(ImportError) as ctx:
            _deps.require("a_module_that_does_not_exist", "requirements-web.txt")
        msg = str(ctx.exception)
        self.assertIn("requirements-web.txt", msg)
        self.assertIn("requirements-dev.txt", msg)
        self.assertIn("a_module_that_does_not_exist", msg)

    def test_original_importerror_is_not_chained_into_noise(self):
        # `from None` keeps the traceback about the missing dependency, not
        # about importlib's internals.
        with self.assertRaises(ImportError) as ctx:
            _deps.require("a_module_that_does_not_exist", "requirements-web.txt")
        self.assertIsNone(ctx.exception.__cause__)


if __name__ == "__main__":
    unittest.main()
