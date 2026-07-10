import unittest

import _path  # noqa: F401  (sys.path shim)
from engine import formats


class FormatFilesizeTests(unittest.TestCase):
    def test_kb(self):
        self.assertEqual(formats.format_filesize(1024), "1.0 KB")

    def test_just_below_1_mib_stays_kb(self):
        # 1 MiB - 1 byte must NOT round up into MB (V3.0 boundary fix).
        self.assertTrue(formats.format_filesize(1_048_575).endswith("KB"))

    def test_exactly_1_mib_is_mb(self):
        self.assertEqual(formats.format_filesize(1_048_576), "1.0 MB")

    def test_exactly_1_gib_is_gb(self):
        self.assertEqual(formats.format_filesize(1_073_741_824), "1.00 GB")


class FormatStringTests(unittest.TestCase):
    def test_best(self):
        s = formats.build_ydl_format_string("best", "mp4")
        self.assertIn("bestvideo[ext=mp4]", s)
        self.assertTrue(s.endswith("/best"))

    def test_worst(self):
        self.assertEqual(
            formats.build_ydl_format_string("worst", "mp4"),
            "worstvideo+worstaudio/worst",
        )

    def test_height_capped(self):
        s = formats.build_ydl_format_string("720p", "mp4")
        self.assertIn("height<=720", s)


class PlatformTests(unittest.TestCase):
    def test_is_douyin(self):
        self.assertTrue(formats.is_douyin("https://v.douyin.com/abc"))
        self.assertFalse(formats.is_douyin("https://youtube.com/watch?v=x"))

    def test_is_tiktok(self):
        self.assertTrue(formats.is_tiktok("https://www.tiktok.com/@u/video/1"))

    def test_headers_douyin(self):
        h = formats.platform_headers("https://www.douyin.com/video/1")
        self.assertEqual(h["Referer"], "https://www.douyin.com/")

    def test_headers_tiktok(self):
        h = formats.platform_headers("https://www.tiktok.com/@u/video/1")
        self.assertIn("tiktok.com", h["Referer"])

    def test_headers_other_empty(self):
        self.assertEqual(formats.platform_headers("https://youtube.com/x"), {})


if __name__ == "__main__":
    unittest.main()
