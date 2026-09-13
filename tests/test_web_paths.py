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

    def test_run_queue_with_escaping_path_returns_400(self):
        r = self.client.post("/api/run_queue", json={"tasks": [
            {"kind": "convert", "src_path": "../../x.mkv", "dst_path": "x.mp4"}]})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
