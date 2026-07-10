import os
import unittest

import _path  # noqa: F401
from engine import Converter, ConvertJob


class MakeJobTests(unittest.TestCase):
    def test_dst_path_uses_save_path_and_fmt(self):
        conv = Converter(save_path=os.path.join("out", "dir"), dst_fmt="mp4")
        job = conv.make_job(os.path.join("in", "clip.mkv"))
        self.assertEqual(job.src_path, os.path.join("in", "clip.mkv"))
        self.assertEqual(job.dst_path, os.path.join("out", "dir", "clip.mp4"))
        self.assertEqual(job.status, "pending")


class ConvertOneTests(unittest.TestCase):
    def test_missing_ffmpeg_sets_no_ffmpeg(self):
        logs = []
        conv = Converter(
            save_path="out", dst_fmt="mp4",
            log_cb=lambda level, key, **fmt: logs.append((level, key)),
            ffmpeg_bin="___definitely_not_a_real_ffmpeg___",
        )
        job = ConvertJob(src_path="a.mkv", dst_path=os.path.join("out", "a.mp4"))
        conv.convert_one(job)
        self.assertEqual(job.status, "no_ffmpeg")
        self.assertIn(("err", "log_no_ffmpeg"), logs)

    def test_job_update_cb_fires(self):
        seen = []
        conv = Converter(
            save_path="out", dst_fmt="mp4",
            job_update_cb=lambda j: seen.append(j.status),
            ffmpeg_bin="___definitely_not_a_real_ffmpeg___",
        )
        job = ConvertJob(src_path="a.mkv", dst_path="out/a.mp4")
        conv.convert_one(job)
        # first "converting", then final "no_ffmpeg"
        self.assertEqual(seen[0], "converting")
        self.assertEqual(seen[-1], "no_ffmpeg")


if __name__ == "__main__":
    unittest.main()
