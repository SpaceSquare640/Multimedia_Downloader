"""
TaskQueue — a unified, inspectable queue of download + convert operations.

This is the NEW V4.0 capability that serves the AI assistant's
"advise -> confirm -> execute" model (decision D4): the AI produces a plan as a
list of :class:`Task` objects, the user reviews it, and only then does
:meth:`TaskQueue.run` execute them sequentially, reporting per-task status and
honouring a cooperative stop flag.

Each task delegates to the same :class:`~engine.downloader.Downloader` /
:class:`~engine.converter.Converter` used elsewhere, so behaviour stays
identical — the queue only orchestrates ordering, status, and cancellation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from .converter import Converter
from .downloader import Downloader
from .options import ConvertJob, DownloadOptions, LogCallback
from typing import Callable

#: ``(task) -> None`` — a Task whose status just changed
TaskUpdateCallback = Callable[["Task"], None]

DOWNLOAD = "download"
CONVERT = "convert"


@dataclass
class Task:
    """
    One unit of work in a :class:`TaskQueue`.

    ``kind`` selects which fields are meaningful:
    * ``"download"`` uses ``url`` + ``options``
    * ``"convert"``  uses ``src_path`` + ``dst_path``
    """
    kind:     str
    label:    str = ""
    status:   str = "pending"   # pending | running | done | error | skipped
    error:    str = ""
    # download
    url:      Optional[str] = None
    options:  Optional[DownloadOptions] = None
    # convert
    src_path: Optional[str] = None
    dst_path: Optional[str] = None


# ── Task factories — the clean way for a planner to build a plan ──────────────

def download_task(url: str, options: DownloadOptions, label: str = "") -> Task:
    return Task(kind=DOWNLOAD, url=url, options=options,
                label=label or url)


def convert_task(src_path: str, dst_path: str, label: str = "") -> Task:
    return Task(kind=CONVERT, src_path=src_path, dst_path=dst_path,
                label=label or os.path.basename(src_path))


class TaskQueue:
    """
    Sequentially execute a reviewed list of :class:`Task` objects.

    Callbacks
    ---------
    log_cb(level, key, **fmt)
        Queue-level log lines plus the delegated download/convert lines.
    task_update_cb(task)
        Called whenever a task's status changes.
    """

    def __init__(
        self,
        log_cb:         Optional[LogCallback]        = None,
        task_update_cb: Optional[TaskUpdateCallback] = None,
        ffmpeg_bin:     str = "ffmpeg",
    ) -> None:
        self.log_cb         = log_cb
        self.task_update_cb = task_update_cb
        self.ffmpeg_bin     = ffmpeg_bin
        self._stop          = False

    def stop(self) -> None:
        """Request cooperative cancellation. Pending tasks become ``skipped``."""
        self._stop = True

    def run(self, tasks: list[Task]) -> list[Task]:
        """Execute every task in order. Returns the same list with final status."""
        self._stop = False
        total = len(tasks)
        self._log("info", "log_queue_start", n=total)

        ok = fail = 0
        for i, task in enumerate(tasks, start=1):
            if self._stop:
                for rest in tasks[i - 1:]:
                    if rest.status == "pending":
                        self._set_status(rest, "skipped")
                self._log("warn", "log_queue_stopped")
                break

            self._run_task(task, i, total)
            if task.status == "done":
                ok += 1
            else:
                fail += 1

        self._log("ok", "log_queue_done", ok=ok, fail=fail, t=total)
        return tasks

    # ── Internal ──────────────────────────────────────────────────────────────
    def _run_task(self, task: Task, index: int, total: int) -> None:
        self._set_status(task, "running")

        if task.kind == DOWNLOAD:
            if not task.url or task.options is None:
                self._set_status(task, "error", "download task missing url/options")
                return
            dl = Downloader(task.options, log_cb=self.log_cb)
            try:
                dl.download_one(task.url)
                self._set_status(task, "done")
            except Exception as e:
                self._set_status(task, "error", str(e))

        elif task.kind == CONVERT:
            if not task.src_path or not task.dst_path:
                self._set_status(task, "error", "convert task missing src/dst path")
                return
            conv = Converter(
                save_path=os.path.dirname(task.dst_path),
                dst_fmt=os.path.splitext(task.dst_path)[1].lstrip("."),
                log_cb=self.log_cb,
                ffmpeg_bin=self.ffmpeg_bin,
            )
            job = ConvertJob(src_path=task.src_path, dst_path=task.dst_path)
            conv.convert_one(job, index=index, total=total)
            if job.status == "done":
                self._set_status(task, "done")
            else:
                self._set_status(task, "error", job.error)

        else:
            self._set_status(task, "error", f"unknown task kind: {task.kind!r}")

    def _set_status(self, task: Task, status: str, error: str = "") -> None:
        task.status = status
        if error:
            task.error = error
        if self.task_update_cb:
            self.task_update_cb(task)

    def _log(self, level: str, key: str, **fmt) -> None:
        if self.log_cb:
            self.log_cb(level, key, **fmt)
