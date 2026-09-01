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


class ConvertBatchSummaryTests(unittest.TestCase):
    """Same fix as the download batch: the closing line must not claim success
    when every conversion failed."""

    def _batch_summary(self, n=3):
        logs = []
        conv = Converter(
            save_path="out", dst_fmt="mp4",
            log_cb=lambda level, key, **fmt: logs.append((level, key, fmt)),
            ffmpeg_bin="___definitely_not_a_real_ffmpeg___",
        )
        conv.convert_batch(["a%d.mkv" % i for i in range(n)])
        return [l for l in logs if l[1].startswith("log_all_")]

    def test_all_fail_logs_error_not_ok(self):
        summary = self._batch_summary()
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0][0], "err")
        self.assertEqual(summary[0][1], "log_all_convert_failed")
        self.assertEqual(summary[0][2], {"t": 3})

    def test_stopped_batch_does_not_count_untouched_jobs_as_failures(self):
        logs = []
        conv = Converter(
            save_path="out", dst_fmt="mp4",
            log_cb=lambda level, key, **fmt: logs.append((level, key, fmt)),
            ffmpeg_bin="___definitely_not_a_real_ffmpeg___",
        )
        # Stop right after the first job runs; jobs 2 and 3 stay "pending".
        conv.job_update_cb = lambda j: conv.stop() if j.status != "converting" else None
        conv.convert_batch(["a.mkv", "b.mkv", "c.mkv"])
        summary = [l for l in logs if l[1].startswith("log_all_")]
        self.assertEqual(len(summary), 1)
        # Only the one job that ran is counted -- not all three.
        self.assertEqual(summary[0][2], {"t": 1})


if __name__ == "__main__":
    unittest.main()
