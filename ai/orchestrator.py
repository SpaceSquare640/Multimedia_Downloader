"""
Multi-model orchestration for the AI assistant.

Flow (see Obsidian `System_Architecture/V4.0 System Architecture.md` §4):

    user request
        -> PLANNER    drafts a batch plan (what files, what params)
        -> EXECUTOR   turns the plan into concrete, schema-valid tasks
        -> guard      deterministic safety/shape check (defense in depth)
        -> CHECKER    reviews the final tasks against the request, advisory
        -> (show plan to user, AWAIT CONFIRM)          <-- D4 permission gate
        -> engine executes the confirmed tasks (via engine.queue.TaskQueue)
        -> SUMMARIZER condenses the results afterwards

``Orchestrator.plan()`` NEVER touches the filesystem, downloads anything, or
runs ffmpeg — it only talks to OpenRouter and returns a plan for the caller to
show the user. Execution happens separately, only after explicit confirmation.

The user's OpenRouter API key is supplied at call time (from the Tauri secure
layer); it is never persisted by this module.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Optional

from engine.formats import AUDIO_FORMATS, BROWSERS, QUALITY_PRESETS, VIDEO_FORMATS
from engine.options import LogCallback

from .models import CHECKER, EXECUTOR, OPENROUTER_BASE_URL, PLANNER, SUMMARIZER, Model


class OrchestratorError(RuntimeError):
    """Raised for any failure talking to OpenRouter or parsing its replies."""


#: ``(url, payload, api_key) -> parsed_json_response`` — injectable for tests.
Transport = Callable[[str, dict, str], dict]


def _default_transport(url: str, payload: dict, api_key: str) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise OrchestratorError(f"OpenRouter HTTP {e.code}: {body[:300]}") from e
    except urllib.error.URLError as e:
        raise OrchestratorError(f"OpenRouter request failed: {e.reason}") from e


def _extract_json(text: str) -> dict:
    """Pull the first balanced top-level ``{...}`` object out of a model reply."""
    start = text.find("{")
    if start == -1:
        raise OrchestratorError("model reply had no JSON object")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError as e:
                    raise OrchestratorError(f"model reply had invalid JSON: {e}") from e
    raise OrchestratorError("model reply had unbalanced JSON")


_TASK_SCHEMA_HINT = """Return ONLY a JSON object (no prose, no markdown fences) shaped like:
{
  "summary": "one short sentence describing the plan",
  "tasks": [
    {"kind": "download", "label": "...", "url": "...",
     "options": {"save_path": "...", "mode": "video", "video_fmt": "mp4",
                 "audio_fmt": "mp3", "quality": "best", "browser": "none"}},
    {"kind": "convert", "label": "...", "src_path": "...", "dst_path": "..."}
  ]
}
Every task is either kind "download" (needs url + options) or kind "convert"
(needs src_path + dst_path). Only use values from the known lists below."""


def _validate_tasks(raw_tasks) -> tuple[list[dict], list[str]]:
    """
    Deterministic safety/shape guard — defense in depth under the LLM checker.

    Drops malformed tasks (recording a warning) and clamps any format/quality/
    browser value that isn't in the known catalogue to a safe default, rather
    than trusting the model's output verbatim.
    """
    warnings: list[str] = []
    clean: list[dict] = []
    for i, t in enumerate(raw_tasks if isinstance(raw_tasks, list) else []):
        if not isinstance(t, dict):
            warnings.append(f"task {i + 1}: skipped (not an object)")
            continue
        kind = t.get("kind")
        label = str(t.get("label") or f"task {i + 1}")

        if kind == "download":
            url = t.get("url")
            options = t.get("options") if isinstance(t.get("options"), dict) else {}
            if not url or not isinstance(url, str):
                warnings.append(f"{label}: skipped (missing url)")
                continue
            if not options.get("save_path"):
                warnings.append(f"{label}: skipped (missing save_path)")
                continue
            mode = options.get("mode") if options.get("mode") in ("video", "audio") else "video"
            video_fmt = options.get("video_fmt") if options.get("video_fmt") in VIDEO_FORMATS else "mp4"
            audio_fmt = options.get("audio_fmt") if options.get("audio_fmt") in AUDIO_FORMATS else "mp3"
            quality = options.get("quality") if options.get("quality") in QUALITY_PRESETS else "best"
            browser = options.get("browser") if options.get("browser") in BROWSERS else "none"
            clean.append({
                "kind": "download", "label": label, "url": url,
                "options": {
                    "save_path": options["save_path"], "mode": mode,
                    "video_fmt": video_fmt, "audio_fmt": audio_fmt,
                    "quality": quality, "browser": browser,
                },
            })

        elif kind == "convert":
            src = t.get("src_path")
            dst = t.get("dst_path")
            if not src or not dst:
                warnings.append(f"{label}: skipped (missing src_path/dst_path)")
                continue
            clean.append({"kind": "convert", "label": label, "src_path": src, "dst_path": dst})

        else:
            warnings.append(f"{label}: skipped (unknown task kind {kind!r})")

    return clean, warnings


class Orchestrator:
    """Coordinates the four free OpenRouter models (see :mod:`ai.models`)."""

    def __init__(
        self,
        api_key: str,
        transport: Transport = _default_transport,
        log_cb: Optional[LogCallback] = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise OrchestratorError("missing OpenRouter API key")
        self._api_key = api_key
        self._transport = transport
        self._log = log_cb or (lambda *a, **k: None)

    def _call(self, model: Model, system: str, user: str) -> str:
        payload = {
            "model": model.slug,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        resp = self._transport(f"{OPENROUTER_BASE_URL}/chat/completions", payload, self._api_key)
        try:
            return resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise OrchestratorError(f"unexpected response from {model.slug}: {resp}") from e

    def _catalogue(self, context: dict) -> str:
        return (
            f"Known video formats: {VIDEO_FORMATS}\n"
            f"Known audio formats: {AUDIO_FORMATS}\n"
            f"Known quality presets: {QUALITY_PRESETS}\n"
            f"Known browsers: {BROWSERS}\n"
            f"Default save_path if the user didn't specify one: {context.get('save_path', '')!r}\n"
            f"Default browser if the user didn't specify one: {context.get('browser', 'none')!r}\n"
        )

    def plan(self, user_request: str, context: Optional[dict] = None) -> dict:
        """
        Return a proposed batch plan for user confirmation. Never executes
        anything — the caller is responsible for the D4 confirm gate and for
        actually running the returned tasks (e.g. via ``engine.queue.TaskQueue``).
        """
        context = context or {}
        catalogue = self._catalogue(context)

        self._log("info", "log_ai_planning_start")
        draft_raw = self._call(
            PLANNER,
            "You are a planning assistant for a media downloader/converter app. "
            "Given a user's request, draft a batch plan of download/convert tasks.\n"
            + catalogue + "\n" + _TASK_SCHEMA_HINT,
            user_request,
        )
        draft = _extract_json(draft_raw)

        self._log("info", "log_ai_executing")
        exec_raw = self._call(
            EXECUTOR,
            "You refine a draft task plan into strictly valid tasks. Fix any format/"
            "quality/browser value that is not in the known lists (use the closest "
            "valid one, or 'best'/'none'). Keep the same tasks and intent.\n"
            + catalogue + "\n" + _TASK_SCHEMA_HINT,
            json.dumps(draft),
        )
        refined = _extract_json(exec_raw)

        tasks, warnings = _validate_tasks(refined.get("tasks", []))

        self._log("info", "log_ai_checking")
        if tasks:
            try:
                check_raw = self._call(
                    CHECKER,
                    "You review a finalized task plan for a media downloader/converter "
                    'app against the user\'s original request. Reply with ONLY a JSON '
                    'object: {"ok": true|false, "warnings": ["..."]}. Flag anything that '
                    "looks like it does not match the request, or touches unexpected files.",
                    f"User request: {user_request}\nFinal tasks: {json.dumps(tasks)}",
                )
                verdict = _extract_json(check_raw)
                warnings.extend(str(w) for w in verdict.get("warnings", []))
            except OrchestratorError:
                pass  # the checker is advisory only; a bad reply just skips extra warnings

        self._log("ok", "log_ai_plan_ready", n=len(tasks))
        return {
            "summary": refined.get("summary") or draft.get("summary") or user_request,
            "tasks": tasks,
            "warnings": warnings,
        }

    def summarize(self, results: list[dict]) -> str:
        """Ask SUMMARIZER for a short, human-readable recap of a finished run."""
        text = self._call(
            SUMMARIZER,
            "Summarize this batch run for the user in ONE short plain-text sentence "
            "(no JSON, no markdown).",
            json.dumps(results),
        )
        return text.strip()
