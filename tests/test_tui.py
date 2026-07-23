"""Smoke tests for the Textual terminal UI (tui/). Headless via App.run_test()."""
import _path  # noqa: F401  (sys.path shim)

import os
import tempfile
import time
import unittest
from unittest.mock import patch

import i18n
from engine import Downloader
from tui.app import MultimediaDownloaderApp
from tui.convert_tab import ConvertTab
from tui.download_tab import DownloadTab
from tui.log_tab import LogTab


def _fake_download_batch(self, urls):
    self.item_start_cb(1, len(urls), urls[0])
    self.log_cb("info", "log_item_downloading", i=1, t=len(urls), url=urls[0])
    self.progress_cb(50.0, "1.2MB/s", "00:05")
    self.progress_cb(100.0, "--", "--")
    self.log_cb("ok", "log_item_done", i=1, t=len(urls))
    return [(urls[0], True, "")]


class TuiTests(unittest.IsolatedAsyncioTestCase):
    async def test_app_starts_with_three_tabs(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            self.assertIsNotNone(app.query_one(DownloadTab))
            self.assertIsNotNone(app.query_one(ConvertTab))
            self.assertIsNotNone(app.query_one(LogTab))

    async def test_dark_mode_toggle(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            before = app.theme
            await pilot.press("d")
            await pilot.pause()
            self.assertNotEqual(app.theme, before)

    async def test_convert_add_and_remove_file(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            cv = app.query_one(ConvertTab)
            cv.query_one("#file-paths").text = "clip.mkv"
            cv._add_files()
            self.assertEqual(cv._files, ["clip.mkv"])
            cv._remove_selected()
            self.assertEqual(cv._files, [])

    async def test_convert_add_multiple_files_at_once(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            cv = app.query_one(ConvertTab)
            cv.query_one("#file-paths").text = "a.mkv\nb.mov\n\nc.mp4"
            cv._add_files()
            self.assertEqual(cv._files, ["a.mkv", "b.mov", "c.mp4"])
            self.assertEqual(len(cv._item_widgets), 3)

    async def test_convert_duplicate_paths_get_independent_rows(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            cv = app.query_one(ConvertTab)
            cv.query_one("#file-paths").text = "dup.mkv\ndup.mkv"
            cv._add_files()

            job_row = {}

            class FakeJob:
                def __init__(self, src_path, status):
                    self.src_path = src_path
                    self.status = status

            jobs = [FakeJob("dup.mkv", "pending"), FakeJob("dup.mkv", "pending")]
            for job in jobs:
                row = job_row.setdefault(id(job), len(job_row))
                job.status = "done"
                cv._mark_item(row, job.status)

            self.assertEqual(job_row[id(jobs[0])], 0)
            self.assertEqual(job_row[id(jobs[1])], 1)

    async def test_download_mode_toggle_shows_correct_fields(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            dl = app.query_one(DownloadTab)
            dl.mode = "audio"
            await pilot.pause()
            self.assertTrue(dl.query_one("#audio-fields").display)
            self.assertFalse(dl.query_one("#video-fields").display)
            dl.mode = "video"
            await pilot.pause()
            self.assertFalse(dl.query_one("#audio-fields").display)
            self.assertTrue(dl.query_one("#video-fields").display)

    async def test_log_handles_bracket_content_without_crashing(self):
        # yt-dlp/ffmpeg output routinely contains literal "[...]" (site name
        # prefixes, codec/address tags) -- these must never be parsed as Rich
        # markup (which would silently swallow them, or in some cases raise
        # MarkupError and crash the whole app).
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            lg = app.query_one(LogTab)
            app.log_line("err", "log_item_error", i=1, t=1,
                         err="[youtube] dQw4w9WgXcQ: Sign in to confirm your age")
            app.log_line("info", "log_convert_start", i=1, t=1,
                         src="Song [HD].mkv", dst="Song [HD] [/].mp4")
            await pilot.pause()
            self.assertIn("[youtube]", lg._entries[0][2])
            self.assertIn("[/]", lg._entries[1][2])

    async def test_log_append_filter_and_clear_confirm(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            lg = app.query_one(LogTab)
            app.log_line("info", "log_start_batch", n=3)
            app.log_line("err", "log_item_error", i=1, t=3, err="boom")
            self.assertEqual(len(lg._entries), 2)

            lg.query_one("#level").value = "err"
            lg._refilter()
            await pilot.pause()

            # Clear requires confirmation -- pushing the dialog then dismissing
            # with False must NOT clear the entries.
            lg._confirm_clear()
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            self.assertEqual(len(lg._entries), 2)

            # Confirming actually clears.
            lg._entries.clear()
            lg.query_one("#console").clear()
            self.assertEqual(len(lg._entries), 0)

    async def test_log_export_writes_a_file(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            lg = app.query_one(LogTab)
            app.log_line("ok", "log_all_done", t=1)
            with tempfile.TemporaryDirectory() as tmp:
                cwd = os.getcwd()
                os.chdir(tmp)
                try:
                    lg._export()
                    files = [f for f in os.listdir(tmp) if f.startswith("mmdl_log_")]
                    self.assertEqual(len(files), 1)
                finally:
                    os.chdir(cwd)

    async def test_download_worker_updates_progress_and_log(self):
        app = MultimediaDownloaderApp(i18n.Translator("en"))
        async with app.run_test() as pilot:
            dl = app.query_one(DownloadTab)
            lg = app.query_one(LogTab)
            dl.query_one("#urls").text = "https://example.com/video"
            dl.query_one("#save-path").value = "."

            with patch.object(Downloader, "download_batch", _fake_download_batch):
                dl._start()
                for _ in range(50):
                    await pilot.pause(0.05)
                    if dl.query_one("#stop").disabled:
                        break

            self.assertFalse(dl.query_one("#start").disabled)
            self.assertTrue(dl.query_one("#stop").disabled)
            self.assertEqual(dl.query_one("#progress").progress, 100.0)
            self.assertGreaterEqual(len(lg._entries), 2)


if __name__ == "__main__":
    unittest.main()
