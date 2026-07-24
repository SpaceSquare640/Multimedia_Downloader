import unittest
from unittest.mock import MagicMock, patch

import _path  # noqa: F401
from engine import DownloadOptions, Downloader


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


if __name__ == "__main__":
    unittest.main()
