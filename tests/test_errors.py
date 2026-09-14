"""
Tests for engine/errors.py — the single place that decides what a failure means.

Behaviour used to branch on substrings scattered across modules. Centralising
it does not make the string matching robust, so these tests exist to make it
*visible*: if an upstream library rewords a message, a test here should be what
tells you, rather than a quietly reduced success rate in the field.
"""
from __future__ import annotations

import unittest

import _path  # noqa: F401  — puts the project root on sys.path

from engine.errors import ErrorKind, classify, is_stale_tool


class ClassifyTests(unittest.TestCase):
    def test_missing_ffmpeg_detected_by_type_not_message(self):
        # The message is deliberately unhelpful: type alone must be enough.
        self.assertIs(classify(FileNotFoundError("")), ErrorKind.NO_FFMPEG)

    def test_type_wins_over_message(self):
        # A FileNotFoundError whose text contains a transient marker is still
        # NO_FFMPEG -- type is checked first for a reason.
        exc = FileNotFoundError("403 while looking for ffmpeg")
        self.assertIs(classify(exc), ErrorKind.NO_FFMPEG)

    def test_403_is_transient(self):
        self.assertIs(classify(RuntimeError("HTTP Error 403: Forbidden")),
                      ErrorKind.TRANSIENT)

    def test_forbidden_without_code_is_transient(self):
        self.assertIs(classify(RuntimeError("Forbidden")), ErrorKind.TRANSIENT)

    def test_5xx_is_transient(self):
        self.assertIs(classify(RuntimeError("HTTP Error 503: Service Unavailable")),
                      ErrorKind.TRANSIENT)

    def test_unrecognised_is_unknown(self):
        self.assertIs(classify(ValueError("something else entirely")),
                      ErrorKind.UNKNOWN)

    def test_404_is_not_transient(self):
        # Retrying a genuine 404 just wastes the user's time.
        self.assertIs(classify(RuntimeError("HTTP Error 404: Not Found")),
                      ErrorKind.UNKNOWN)

    # ── Documented non-behaviour ─────────────────────────────────────────────
    # These pin what we deliberately do NOT treat as transient. If either is
    # ever added, it needs its own backoff -- these tests should then be
    # updated consciously rather than silently starting to fail.
    def test_rate_limit_is_not_transient_today(self):
        self.assertIs(classify(RuntimeError("HTTP Error 429: Too Many Requests")),
                      ErrorKind.UNKNOWN)

    def test_timeout_is_not_transient_today(self):
        self.assertIs(classify(TimeoutError("timed out")), ErrorKind.UNKNOWN)


class StaleToolTests(unittest.TestCase):
    """
    STALE_TOOL is a transition, not a property: the same 403 means "retry" on
    the first attempt and "your downloader is out of date" once retrying has
    failed. Only the retry loop knows which, so this is a separate predicate.
    """

    def test_403_after_retries_points_at_a_stale_tool(self):
        self.assertTrue(is_stale_tool(RuntimeError("HTTP Error 403: Forbidden")))

    def test_5xx_does_not(self):
        # A 5xx that never recovered is the server's problem, not ours --
        # telling the user to update the app would be actively misleading.
        self.assertFalse(is_stale_tool(RuntimeError("HTTP Error 503")))

    def test_unknown_error_does_not(self):
        self.assertFalse(is_stale_tool(ValueError("boom")))

    def test_missing_ffmpeg_does_not(self):
        self.assertFalse(is_stale_tool(FileNotFoundError("ffmpeg")))


class EnumTests(unittest.TestCase):
    def test_serialises_as_plain_string(self):
        # str-subclass, so it survives json.dumps if it ever crosses IPC.
        self.assertEqual(ErrorKind.TRANSIENT.value, "transient")
        self.assertEqual(f"{ErrorKind.NO_FFMPEG.value}", "no_ffmpeg")

    def test_no_members_without_a_consumer(self):
        # Guards the decision to keep the enum minimal: BAD_INPUT/PERMISSION
        # were left out until something actually branches on them. Adding a
        # member should be a deliberate act that updates this test.
        self.assertEqual(
            {k.name for k in ErrorKind},
            {"TRANSIENT", "STALE_TOOL", "NO_FFMPEG", "UNKNOWN"},
        )


if __name__ == "__main__":
    unittest.main()
