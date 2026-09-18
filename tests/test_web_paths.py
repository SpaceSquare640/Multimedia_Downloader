"""
Tests for the web backend's path confinement (web_app.py).

Every path in a request to the web app comes from the browser, and the engine
reads and writes wherever it is pointed. Unconfined, a LAN-exposed server would
let any client write anywhere the process can write and pull any media file on
the host back out through /files/. These tests pin the confinement that closed
that, including the documented opt-out.
"""
from __future__ import annotations

import os
import tempfile
import unittest

import _path  # noqa: F401  — puts the project root on sys.path

# web_app reads MMDL_DOWNLOADS at import time, so point it somewhere disposable
# before importing it.
_TMP = tempfile.mkdtemp(prefix="mmdl-test-")
os.environ["MMDL_DOWNLOADS"] = _TMP

try:
    import web_app
except ImportError:  # pragma: no cover - flask missing (see requirements-web.txt)
    web_app = None


@unittest.skipIf(web_app is None, "flask not installed")
class ConfineTests(unittest.TestCase):
    def setUp(self):
        # Each test starts from the secure default, whatever the environment
        # the suite happens to run in says.
        self._saved = web_app.ALLOW_ABSOLUTE_PATHS
        web_app.ALLOW_ABSOLUTE_PATHS = False
        os.makedirs(web_app.DOWNLOADS_DIR, exist_ok=True)

    def tearDown(self):
        web_app.ALLOW_ABSOLUTE_PATHS = self._saved

    @property
    def root(self) -> str:
        return os.path.realpath(web_app.DOWNLOADS_DIR)

    # ── the allowed cases ────────────────────────────────────────────────────
    def test_blank_save_path_uses_downloads_dir(self):
        self.assertEqual(web_app._save_path(""), web_app.DOWNLOADS_DIR)
        self.assertEqual(web_app._save_path(None), web_app.DOWNLOADS_DIR)

    def test_relative_path_resolves_inside_downloads(self):
        got = web_app._save_path("clips")
        self.assertEqual(got, os.path.join(self.root, "clips"))

    def test_nested_relative_path_allowed(self):
        got = web_app._save_path("a/b/c")
        self.assertTrue(got.startswith(self.root + os.sep))

    def test_downloads_root_itself_allowed(self):
        self.assertEqual(web_app._confine("."), self.root)

    # ── the rejected cases ───────────────────────────────────────────────────
    def test_parent_traversal_rejected(self):
        with self.assertRaises(web_app.UnsafePath):
            web_app._save_path("../../etc")

    def test_absolute_path_outside_rejected(self):
        outside = "C:\\Windows\\Temp" if os.name == "nt" else "/etc"
        with self.assertRaises(web_app.UnsafePath):
            web_app._save_path(outside)

    def test_rejection_message_names_the_opt_out(self):
        # A legitimate local user who hits this needs to know the way out.
        with self.assertRaises(web_app.UnsafePath) as ctx:
            web_app._save_path("../elsewhere")
        self.assertIn("MMDL_ALLOW_ABSOLUTE_PATHS", str(ctx.exception))

    def test_convert_inputs_are_confined(self):
        with self.assertRaises(web_app.UnsafePath):
            web_app._confine_all(["../../secrets.mp4"])
        self.assertEqual(len(web_app._confine_all(["a.mkv", "sub/b.mkv"])), 2)

    # ── AI task lists (run_queue) ────────────────────────────────────────────
    def test_task_download_save_path_confined(self):
        tasks = [{"kind": "download", "url": "u",
                  "options": {"save_path": "out", "mode": "video"}}]
        got = web_app._confine_tasks(tasks)
        self.assertTrue(got[0]["options"]["save_path"].startswith(self.root))
        # the caller's dict must not be mutated in place
        self.assertEqual(tasks[0]["options"]["save_path"], "out")

    def test_task_convert_paths_confined(self):
        got = web_app._confine_tasks(
            [{"kind": "convert", "src_path": "a.mkv", "dst_path": "a.mp4"}])
        self.assertTrue(got[0]["src_path"].startswith(self.root))
        self.assertTrue(got[0]["dst_path"].startswith(self.root))

    def test_task_escaping_path_rejected(self):
        with self.assertRaises(web_app.UnsafePath):
            web_app._confine_tasks(
                [{"kind": "convert", "src_path": "../../x.mkv", "dst_path": "x.mp4"}])

    # ── the opt-out ──────────────────────────────────────────────────────────
    def test_opt_out_restores_arbitrary_paths(self):
        web_app.ALLOW_ABSOLUTE_PATHS = True
        outside = "C:\\Windows\\Temp" if os.name == "nt" else "/etc"
        self.assertEqual(web_app._save_path(outside), outside)
        self.assertEqual(web_app._confine_all([outside]), [outside])


@unittest.skipIf(web_app is None, "flask not installed")
class FormatAndBrowserTests(unittest.TestCase):
    """
    `dst_fmt` is concatenated into the output path downstream, so an unchecked
    one escapes the confined directory without ever passing through _confine().
    That is exactly how the first version of this confinement was bypassed.
    """

    def setUp(self):
        self._saved = web_app.ALLOW_ABSOLUTE_PATHS
        web_app.ALLOW_ABSOLUTE_PATHS = False

    def tearDown(self):
        web_app.ALLOW_ABSOLUTE_PATHS = self._saved

    def _fmt(self, value):
        from engine import AUDIO_FORMATS, VIDEO_FORMATS
        return web_app._choice(value, set(VIDEO_FORMATS) | set(AUDIO_FORMATS),
                               "output format", "mp4")

    def test_known_formats_accepted(self):
        for fmt in ("mp4", "mkv", "mp3", "flac"):
            self.assertEqual(self._fmt(fmt), fmt)

    def test_blank_falls_back_to_default(self):
        self.assertEqual(self._fmt(""), "mp4")
        self.assertEqual(self._fmt(None), "mp4")

    def test_traversal_in_format_rejected(self):
        # The original bypass: dst_fmt steered the output path.
        with self.assertRaises(web_app.UnsafePath):
            self._fmt("../../../../Windows/Temp/evil.mp4")

    def test_separators_in_format_rejected(self):
        for bad in ("a/b", r"a\b", "sub/x.mp4"):
            with self.assertRaises(web_app.UnsafePath):
                self._fmt(bad)

    def test_unknown_format_rejected(self):
        with self.assertRaises(web_app.UnsafePath):
            self._fmt("exe")

    def test_unknown_browser_rejected(self):
        with self.assertRaises(web_app.UnsafePath):
            web_app._choice("../etc", {"none", "chrome"}, "browser", "none")

    def test_download_format_catalogues_are_the_engine_s(self):
        # The web layer must not be narrower or wider than what the engine
        # accepts, or one of them is wrong.
        from engine import AUDIO_FORMATS, QUALITY_PRESETS, VIDEO_FORMATS
        for fmt in VIDEO_FORMATS:
            self.assertEqual(
                web_app._choice(fmt, set(VIDEO_FORMATS), "video format", "mp4"),
                fmt)
        for fmt in AUDIO_FORMATS:
            self.assertEqual(
                web_app._choice(fmt, set(AUDIO_FORMATS), "audio format", "mp3"),
                fmt)
        for q in QUALITY_PRESETS:
            self.assertEqual(
                web_app._choice(q, set(QUALITY_PRESETS), "quality", "best"), q)


@unittest.skipIf(web_app is None, "flask not installed")
class CookieFileTests(unittest.TestCase):
    """cookie_file is a server-side path like save_path, and the file most
    likely to be there is the one worth stealing."""

    def setUp(self):
        self._saved = web_app.ALLOW_ABSOLUTE_PATHS
        web_app.ALLOW_ABSOLUTE_PATHS = False

    def tearDown(self):
        web_app.ALLOW_ABSOLUTE_PATHS = self._saved

    def test_cookie_file_is_confined(self):
        got = web_app._confine_tasks([{
            "kind": "download", "url": "u",
            "options": {"save_path": "out", "cookie_file": "jar.txt"}}])
        self.assertTrue(got[0]["options"]["cookie_file"].startswith(
            os.path.realpath(web_app.DOWNLOADS_DIR)))

    def test_cookie_file_outside_rejected(self):
        outside = r"C:\secret.txt" if os.name == "nt" else "/etc/passwd"
        with self.assertRaises(web_app.UnsafePath):
            web_app._confine_tasks([{
                "kind": "download", "url": "u",
                "options": {"save_path": "out", "cookie_file": outside}}])

    def test_task_without_options_still_handled(self):
        got = web_app._confine_tasks([{"kind": "download", "url": "u"}])
        self.assertEqual(len(got), 1)


@unittest.skipIf(web_app is None, "flask not installed")
class EndpointTests(unittest.TestCase):
    """A rejected path must read as a client error, not a server crash."""

    def setUp(self):
        self._saved = web_app.ALLOW_ABSOLUTE_PATHS
        web_app.ALLOW_ABSOLUTE_PATHS = False
        web_app.app.config["TESTING"] = True
        self.client = web_app.app.test_client()

    def tearDown(self):
        web_app.ALLOW_ABSOLUTE_PATHS = self._saved

    def test_convert_with_escaping_path_returns_400(self):
        r = self.client.post("/api/convert",
                             json={"files": ["../../etc/passwd"], "dst_fmt": "mp4"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("outside", r.get_json()["error"])

    def test_convert_with_escaping_format_returns_400(self):
        r = self.client.post("/api/convert",
                             json={"files": ["a.mkv"], "dst_fmt": "../../x.mp4"})
        self.assertEqual(r.status_code, 400)

    def test_run_queue_with_escaping_path_returns_400(self):
        r = self.client.post("/api/run_queue", json={"tasks": [
            {"kind": "convert", "src_path": "../../x.mkv", "dst_path": "x.mp4"}]})
        self.assertEqual(r.status_code, 400)

    def test_download_format_fields_return_400(self):
        # /api/download feeds video_fmt into yt-dlp's merge_output_format --
        # which decides %(ext)s, and so the output path -- and feeds video_fmt
        # and quality into the format-selector string. The engine rejects these
        # too; checking here only turns a 500 into a 400.
        for field, bad in (("video_fmt", "../../x"),
                           ("audio_fmt", "../../x"),
                           ("quality", "0]/all[height>0"),
                           ("mode", "../../x")):
            with self.subTest(field=field):
                r = self.client.post("/api/download",
                                     json={"urls": ["u"], field: bad})
                self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
