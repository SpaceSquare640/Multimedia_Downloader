import unittest

import _path  # noqa: F401
import engine.queue as q
from engine import DownloadOptions, TaskQueue, download_task, convert_task


class FactoryTests(unittest.TestCase):
    def test_download_task(self):
        opts = DownloadOptions(save_path="out")
        t = download_task("http://x/v", opts)
        self.assertEqual(t.kind, "download")
        self.assertEqual(t.url, "http://x/v")
        self.assertIs(t.options, opts)
        self.assertEqual(t.label, "http://x/v")

    def test_convert_task(self):
        t = convert_task("in/clip.mkv", "out/clip.mp4")
        self.assertEqual(t.kind, "convert")
        self.assertEqual(t.label, "clip.mkv")


class _FakeDownloader:
    """Stand-in for engine.queue.Downloader — records URLs, optionally fails."""
    fail_urls: set = set()
    on_download = None  # optional hook(url) for side effects (e.g. stop)
    seen: list = []

    def __init__(self, options, log_cb=None):
        self.options = options

    def download_one(self, url):
        _FakeDownloader.seen.append(url)
        if _FakeDownloader.on_download:
            _FakeDownloader.on_download(url)
        if url in _FakeDownloader.fail_urls:
            raise RuntimeError("boom")


class QueueRunTests(unittest.TestCase):
    def setUp(self):
        _FakeDownloader.fail_urls = set()
        _FakeDownloader.on_download = None
        _FakeDownloader.seen = []
        self._orig = q.Downloader
        q.Downloader = _FakeDownloader

    def tearDown(self):
        q.Downloader = self._orig

    def test_all_success(self):
        opts = DownloadOptions(save_path="out")
        tasks = [download_task(f"http://x/{i}", opts) for i in range(3)]
        updates = []
        tq = TaskQueue(task_update_cb=lambda t: updates.append((t.label, t.status)))
        result = tq.run(tasks)
        self.assertTrue(all(t.status == "done" for t in result))
        self.assertEqual(_FakeDownloader.seen, ["http://x/0", "http://x/1", "http://x/2"])

    def test_one_failure_recorded(self):
        opts = DownloadOptions(save_path="out")
        _FakeDownloader.fail_urls = {"http://x/1"}
        tasks = [download_task(f"http://x/{i}", opts) for i in range(3)]
        tq = TaskQueue()
        result = tq.run(tasks)
        self.assertEqual([t.status for t in result], ["done", "error", "done"])
        self.assertEqual(result[1].error, "boom")

    def test_stop_marks_remaining_skipped(self):
        opts = DownloadOptions(save_path="out")
        tasks = [download_task(f"http://x/{i}", opts) for i in range(4)]
        tq = TaskQueue()
        # Ask the queue to stop while the FIRST task is downloading.
        _FakeDownloader.on_download = lambda url: tq.stop()
        result = tq.run(tasks)
        self.assertEqual(result[0].status, "done")     # first still finishes
        self.assertTrue(all(t.status == "skipped" for t in result[1:]))

    def test_download_task_missing_fields(self):
        bad = q.Task(kind="download", url=None, options=None)
        tq = TaskQueue()
        tq.run([bad])
        self.assertEqual(bad.status, "error")

    def test_unknown_kind(self):
        bad = q.Task(kind="frobnicate")
        tq = TaskQueue()
        tq.run([bad])
        self.assertEqual(bad.status, "error")
        self.assertIn("unknown task kind", bad.error)


if __name__ == "__main__":
    unittest.main()
