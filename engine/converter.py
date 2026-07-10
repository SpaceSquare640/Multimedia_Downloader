"""
Converter — wraps ffmpeg for sequential batch transcoding.

Ported from V3.0 ``core.Converter`` with identical behaviour and log keys.
Refactored so a single file can be converted via :meth:`convert_one` (used by
both :meth:`convert_batch` and the AI-driven :class:`engine.queue.TaskQueue`).
The ffmpeg executable name is parameterised for testability / portability.
"""

from __future__ import annotations

import os
import subprocess
from typing import Iterable, Optional

from .options import ConvertJob, JobUpdateCallback, LogCallback


class Converter:
    """
    Sequentially transcode files using ``ffmpeg``.

    Like :class:`engine.downloader.Downloader`, exposes a stop flag and forwards
    progress through optional callbacks.

    Callbacks
    ---------
    log_cb(level, key, **fmt)
        Forwarded log lines (level: ``info`` | ``ok`` | ``warn`` | ``err``).
    job_update_cb(job)
        Called whenever a job's status changes.
    """

    def __init__(
        self,
        save_path:     str,
        dst_fmt:       str,
        log_cb:        Optional[LogCallback]       = None,
        job_update_cb: Optional[JobUpdateCallback] = None,
        ffmpeg_bin:    str = "ffmpeg",
    ) -> None:
        self.save_path     = save_path
        self.dst_fmt       = dst_fmt
        self.log_cb        = log_cb
        self.job_update_cb = job_update_cb
        self.ffmpeg_bin    = ffmpeg_bin
        self._stop         = False

    # ── Public ──────────────────────────────────────────────────────────────
    def stop(self) -> None:
        self._stop = True

    def make_job(self, src: str) -> ConvertJob:
        """Build a :class:`ConvertJob` mapping ``src`` to a dst in ``save_path``."""
        base = os.path.splitext(os.path.basename(src))[0]
        return ConvertJob(
            src_path=src,
            dst_path=os.path.join(self.save_path, f"{base}.{self.dst_fmt}"),
        )

    def convert_one(self, job: ConvertJob, index: int = 1, total: int = 1) -> ConvertJob:
        """
        Run ffmpeg on a single job, updating its status in place. Never raises —
        failures are recorded on the job (status ``error`` / ``no_ffmpeg``).
        """
        self._log("info", "log_convert_start",
                  i=index, t=total,
                  src=os.path.basename(job.src_path),
                  dst=os.path.basename(job.dst_path))
        self._set_status(job, "converting")

        try:
            result = subprocess.run(
                [self.ffmpeg_bin, "-y", "-i", job.src_path,
                 "-loglevel", "error", job.dst_path],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                self._log("ok", "log_convert_done",
                          i=index, t=total, name=os.path.basename(job.dst_path))
                self._set_status(job, "done")
            else:
                raise RuntimeError(result.stderr[:300] or "ffmpeg error (no output)")

        except FileNotFoundError:
            self._log("err", "log_no_ffmpeg", i=index, t=total)
            self._set_status(job, "no_ffmpeg", error="ffmpeg not found")

        except Exception as e:
            self._log("err", "log_convert_error", i=index, t=total, err=str(e))
            self._set_status(job, "error", error=str(e))

        return job

    def convert_batch(self, src_files: Iterable[str]) -> list[ConvertJob]:
        """Run ffmpeg on each file. Returns the list of jobs with final status."""
        jobs = [self.make_job(src) for src in src_files]
        total = len(jobs)
        self._stop = False

        for i, job in enumerate(jobs, start=1):
            if self._stop:
                self._log("warn", "log_convert_stopped")
                break
            self.convert_one(job, index=i, total=total)

        self._log("ok", "log_all_converted", t=total)
        return jobs

    # ── Internal ──────────────────────────────────────────────────────────────
    def _set_status(self, job: ConvertJob, status: str, error: str = "") -> None:
        job.status = status
        if error:
            job.error = error
        if self.job_update_cb:
            self.job_update_cb(job)

    def _log(self, level: str, key: str, **fmt) -> None:
        if self.log_cb:
            self.log_cb(level, key, **fmt)
