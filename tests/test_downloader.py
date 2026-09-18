import unittest
from unittest.mock import MagicMock, patch

import _path  # noqa: F401
from engine import (
    AUDIO_FORMATS,
    QUALITY_PRESETS,
    VIDEO_FORMATS,
    DownloadOptions,
    Downloader,
)


def _make_downloader(**cbs) -> Downloader:
    opts = DownloadOptions(save_path=".")
    return Downloader(opts, **cbs)


class PlaylistLogTests(unittest.TestCase):
    """`_ydl_hook` should log a playlist-position line once per NEW entry,
    never for a single (non-playlist) download, and never repeatedly for the
    same entry's progress ticks."""

    def test_non_playlist_download_never_logs_playlist_item(self):
        log_cb = MagicMock()
        dl = _make_downloader(log_cb=log_cb)
        dl._ydl_hook({"status": "downloading", "info_dict": {"title": "solo"}})
        dl._ydl_hook({"status": "finished", "info_dict": {"title": "solo"}})
        keys = [c.args[1] for c in log_cb.call_args_list]
        self.assertNotIn("log_playlist_item", keys)

    def test_playlist_entry_logs_once_per_new_index(self):
        log_cb = MagicMock()
        dl = _make_downloader(log_cb=log_cb)

        info1 = {"title": "Track 1", "n_entries": 3, "playlist_index": 1}
        # Several progress ticks for the SAME entry -- must log only once.
        dl._ydl_hook({"status": "downloading", "info_dict": info1})
        dl._ydl_hook({"status": "downloading", "info_dict": info1})
        dl._ydl_hook({"status": "finished", "info_dict": info1})

        info2 = {"title": "Track 2", "n_entries": 3, "playlist_index": 2}
        dl._ydl_hook({"status": "downloading", "info_dict": info2})

        playlist_calls = [c for c in log_cb.call_args_list if c.args[1] == "log_playlist_item"]
        self.assertEqual(len(playlist_calls), 2)
        self.assertEqual(playlist_calls[0].kwargs, {"i": 1, "t": 3, "title": "Track 1"})
        self.assertEqual(playlist_calls[1].kwargs, {"i": 2, "t": 3, "title": "Track 2"})

    def test_download_one_resets_playlist_tracking_between_urls(self):
        # A second, non-playlist URL right after a playlist must not inherit
        # the previous URL's tracked index (each download_one() call is a
        # fresh potential playlist).
        dl = _make_downloader()
        dl._playlist_index_logged = 5
        with patch("engine.downloader.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.download.return_value = None
            dl.download_one("https://example.com/not-a-playlist")
        self.assertIsNone(dl._playlist_index_logged)


class BatchSummaryTests(unittest.TestCase):
    """The batch-summary line must reflect what actually happened. Before this
    was fixed, a batch where every item 403'd still logged `log_all_done` at
    "ok" level -- a green checkmark on total failure (reported by a user)."""

    def _run_batch(self, side_effect):
        log_cb = MagicMock()
        dl = _make_downloader(log_cb=log_cb)
        with patch.object(Downloader, "download_one", side_effect=side_effect):
            results = dl.download_batch(["u1", "u2", "u3"])
        summary = [c for c in log_cb.call_args_list
                   if c.args[1].startswith("log_all_")]
        return results, summary

    def test_all_succeed_logs_ok(self):
        _, summary = self._run_batch(lambda url: None)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0].args[0], "ok")
        self.assertEqual(summary[0].args[1], "log_all_done")

    def test_all_fail_logs_error_not_ok(self):
        def boom(url):
            raise RuntimeError("HTTP Error 403: Forbidden")
        _, summary = self._run_batch(boom)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0].args[0], "err")
        self.assertEqual(summary[0].args[1], "log_all_failed")
        self.assertEqual(summary[0].kwargs, {"t": 3})

    def test_partial_failure_logs_warning_with_counts(self):
        calls = {"n": 0}

        def sometimes(url):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("boom")
        _, summary = self._run_batch(sometimes)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0].args[0], "warn")
        self.assertEqual(summary[0].args[1], "log_all_done_partial")
        self.assertEqual(summary[0].kwargs, {"ok": 2, "fail": 1, "t": 3})


class RetryTests(unittest.TestCase):
    """403s are retried, but a 403 that survives every attempt means a stale
    bundled yt-dlp, not a blip -- say so instead of retrying forever."""

    def test_persistent_403_hints_at_outdated_downloader(self):
        log_cb = MagicMock()
        dl = _make_downloader(log_cb=log_cb)
        with patch.object(Downloader, "download_one",
                          side_effect=RuntimeError("HTTP Error 403: Forbidden")),                 patch("engine.downloader.time.sleep"):
            with self.assertRaises(RuntimeError):
                dl._download_one_with_retry("u1", 1, 1)
        keys = [c.args[1] for c in log_cb.call_args_list]
        self.assertEqual(keys.count("log_item_retry"), 2)
        self.assertIn("log_hint_outdated", keys)

    def test_non_transient_error_is_not_retried_and_gives_no_hint(self):
        log_cb = MagicMock()
        dl = _make_downloader(log_cb=log_cb)
        with patch.object(Downloader, "download_one",
                          side_effect=RuntimeError("no space left on device")),                 patch("engine.downloader.time.sleep"):
            with self.assertRaises(RuntimeError):
                dl._download_one_with_retry("u1", 1, 1)
        keys = [c.args[1] for c in log_cb.call_args_list]
        self.assertNotIn("log_item_retry", keys)
        self.assertNotIn("log_hint_outdated", keys)


class FormatValidationTests(unittest.TestCase):
    """
    `video_fmt` becomes yt-dlp's `merge_output_format`, which decides the
    `%(ext)s` in the output template -- so it helps compose the destination
    path, exactly like `dst_fmt` does for conversion. `video_fmt` and `quality`
    are also interpolated into the format-selector string. All three arrive
    from the network on the web backend, so `_build_ydl_opts` is the point that
    has to reject them.
    """

    def _opts(self, **kw) -> Downloader:
        return Downloader(DownloadOptions(save_path=".", **kw))

    # ── the allowed cases still work ────────────────────────────────────────
    def test_known_video_format_and_quality_accepted(self):
        got = self._opts(mode="video", video_fmt="mkv", quality="720p") \
            ._build_ydl_opts("https://example.com/v")
        self.assertEqual(got["merge_output_format"], "mkv")
        self.assertIn("height<=720", got["format"])

    def test_known_audio_format_accepted(self):
        got = self._opts(mode="audio", audio_fmt="flac") \
            ._build_ydl_opts("https://example.com/v")
        self.assertEqual(got["postprocessors"][0]["preferredcodec"], "flac")

    def test_every_catalogued_format_survives(self):
        # The check must not be narrower than the catalogue the UIs offer.
        for fmt in VIDEO_FORMATS:
            self._opts(mode="video", video_fmt=fmt)._build_ydl_opts("u")
        for fmt in AUDIO_FORMATS:
            self._opts(mode="audio", audio_fmt=fmt)._build_ydl_opts("u")
        for q in QUALITY_PRESETS:
            self._opts(mode="video", quality=q)._build_ydl_opts("u")

    # ── the rejected cases ──────────────────────────────────────────────────
    def test_traversal_in_video_format_rejected(self):
        with self.assertRaises(ValueError):
            self._opts(mode="video", video_fmt="../../../../Windows/Temp/evil") \
                ._build_ydl_opts("u")

    def test_selector_injection_in_quality_rejected(self):
        # Raw interpolation into the yt-dlp format selector, e.g.
        # bestvideo[height<=0]/all[height>0]+bestaudio
        with self.assertRaises(ValueError):
            self._opts(mode="video", quality="0]/all[height>0") \
                ._build_ydl_opts("u")

    def test_unknown_audio_format_rejected(self):
        with self.assertRaises(ValueError):
            self._opts(mode="audio", audio_fmt="../x.sh")._build_ydl_opts("u")

    def test_unused_field_of_the_other_mode_is_not_checked(self):
        # Audio mode never touches video_fmt, so a junk value there must not
        # break an otherwise valid request.
        got = self._opts(mode="audio", audio_fmt="mp3", video_fmt="") \
            ._build_ydl_opts("u")
        self.assertEqual(got["postprocessors"][0]["preferredcodec"], "mp3")


if __name__ == "__main__":
    unittest.main()
