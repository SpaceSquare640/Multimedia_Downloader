import json
import unittest

import _path  # noqa: F401
from ai import models
from ai.models import PLANNER, EXECUTOR, CHECKER, SUMMARIZER, ROSTER
from ai.orchestrator import Orchestrator, OrchestratorError, _extract_json, _validate_tasks


def _reply(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


def _all_live() -> list[dict]:
    """A catalogue in which every default slug is present and free."""
    return [{"id": m.slug, "context_length": m.context,
             "pricing": {"prompt": "0", "completion": "0"}} for m in ROSTER]


def _orch(*args, **kwargs) -> Orchestrator:
    """
    Build an Orchestrator pinned to the default roster.

    Without an injected catalogue the orchestrator resolves against the live
    OpenRouter API, which would make these tests network-dependent and would
    swap in whatever free model exists today (see ai/models.resolve_roster).
    Roster substitution itself is covered in test_models.py.
    """
    kwargs.setdefault("catalog_fetch", _all_live)
    return Orchestrator(*args, **kwargs)


class ExtractJsonTests(unittest.TestCase):
    def test_plain_object(self):
        self.assertEqual(_extract_json('{"a": 1}'), {"a": 1})

    def test_object_with_surrounding_prose(self):
        text = 'Sure, here you go:\n{"a": 1, "b": [1,2]}\nHope that helps!'
        self.assertEqual(_extract_json(text), {"a": 1, "b": [1, 2]})

    def test_markdown_fenced(self):
        text = '```json\n{"a": 1}\n```'
        self.assertEqual(_extract_json(text), {"a": 1})

    def test_no_json_raises(self):
        with self.assertRaises(OrchestratorError):
            _extract_json("no json here")

    def test_unbalanced_raises(self):
        with self.assertRaises(OrchestratorError):
            _extract_json('{"a": 1')


class ValidateTasksTests(unittest.TestCase):
    def test_valid_download_passes(self):
        tasks, warnings = _validate_tasks([
            {"kind": "download", "label": "x", "url": "http://x",
             "options": {"save_path": "out"}},
        ])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(warnings, [])
        self.assertEqual(tasks[0]["options"]["mode"], "video")   # default filled in
        self.assertEqual(tasks[0]["options"]["quality"], "best")

    def test_download_missing_url_dropped(self):
        tasks, warnings = _validate_tasks([
            {"kind": "download", "label": "x", "options": {"save_path": "out"}},
        ])
        self.assertEqual(tasks, [])
        self.assertIn("missing url", warnings[0])

    def test_download_missing_save_path_dropped(self):
        tasks, warnings = _validate_tasks([
            {"kind": "download", "label": "x", "url": "http://x", "options": {}},
        ])
        self.assertEqual(tasks, [])
        self.assertIn("missing save_path", warnings[0])

    def test_bad_format_clamped_not_dropped(self):
        tasks, warnings = _validate_tasks([
            {"kind": "download", "label": "x", "url": "http://x",
             "options": {"save_path": "out", "video_fmt": "totally-fake-format"}},
        ])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["options"]["video_fmt"], "mp4")  # clamped to default

    def test_valid_convert_passes(self):
        tasks, warnings = _validate_tasks([
            {"kind": "convert", "label": "c", "src_path": "a.mkv", "dst_path": "a.mp4"},
        ])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(warnings, [])

    def test_unknown_kind_dropped(self):
        tasks, warnings = _validate_tasks([{"kind": "frobnicate"}])
        self.assertEqual(tasks, [])
        self.assertIn("unknown task kind", warnings[0])

    def test_non_list_input_is_empty(self):
        tasks, warnings = _validate_tasks(None)
        self.assertEqual((tasks, warnings), ([], []))


class OrchestratorInitTests(unittest.TestCase):
    def test_missing_api_key_raises(self):
        with self.assertRaises(OrchestratorError):
            Orchestrator("")
        with self.assertRaises(OrchestratorError):
            Orchestrator("   ")


class PlanPipelineTests(unittest.TestCase):
    def setUp(self):
        models.clear_cache()

    def tearDown(self):
        models.clear_cache()

    def _make(self, planner=None, executor=None, checker=None, log=None):
        calls = []

        def transport(url, payload, api_key):
            calls.append(payload["model"])
            self.assertEqual(api_key, "test-key")
            model = payload["model"]
            if model == PLANNER.slug:
                return _reply(planner)
            if model == EXECUTOR.slug:
                return _reply(executor)
            if model == CHECKER.slug:
                return _reply(checker)
            raise AssertionError(f"unexpected model called: {model}")

        orch = _orch("test-key", transport=transport, log_cb=log)
        return orch, calls

    def test_happy_path(self):
        planner = json.dumps({
            "summary": "download one video",
            "tasks": [{"kind": "download", "label": "vid", "url": "http://x",
                       "options": {"save_path": "out"}}],
        })
        executor = planner  # executor just passes it through unchanged
        checker = json.dumps({"ok": True, "warnings": []})

        logs = []
        orch, calls = self._make(planner, executor, checker,
                                  log=lambda lvl, key, **fmt: logs.append((lvl, key, fmt)))
        result = orch.plan("download http://x")

        self.assertEqual(calls, [PLANNER.slug, EXECUTOR.slug, CHECKER.slug])
        self.assertEqual(result["summary"], "download one video")
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["warnings"], [])
        # log sequence observed
        self.assertEqual([k for _, k, _ in logs],
                          ["log_ai_planning_start", "log_ai_executing",
                           "log_ai_checking", "log_ai_plan_ready"])
        self.assertEqual(logs[-1][2], {"n": 1})

    def test_checker_flags_warning_but_plan_still_returned(self):
        planner = json.dumps({"summary": "s", "tasks": [
            {"kind": "convert", "label": "c", "src_path": "a.mkv", "dst_path": "a.mp4"},
        ]})
        checker = json.dumps({"ok": False, "warnings": ["destination looks unusual"]})
        orch, _ = self._make(planner, planner, checker)
        result = orch.plan("convert a.mkv")
        self.assertEqual(len(result["tasks"]), 1)
        self.assertIn("destination looks unusual", result["warnings"])

    def test_checker_malformed_reply_is_advisory_not_fatal(self):
        planner = json.dumps({"summary": "s", "tasks": [
            {"kind": "convert", "label": "c", "src_path": "a.mkv", "dst_path": "a.mp4"},
        ]})
        orch, _ = self._make(planner, planner, checker="not json at all")
        result = orch.plan("convert a.mkv")
        self.assertEqual(len(result["tasks"]), 1)  # plan still returned

    def test_planner_malformed_json_raises(self):
        orch, _ = self._make(planner="no json", executor="{}", checker="{}")
        with self.assertRaises(OrchestratorError):
            orch.plan("do something")

    def test_guard_drops_invalid_task_end_to_end(self):
        planner = json.dumps({"summary": "s", "tasks": [
            {"kind": "download", "label": "bad", "options": {"save_path": "out"}},  # no url
        ]})
        orch, _ = self._make(planner, planner, json.dumps({"ok": True, "warnings": []}))
        result = orch.plan("do something vague")
        self.assertEqual(result["tasks"], [])
        self.assertTrue(any("missing url" in w for w in result["warnings"]))


class SummarizeTests(unittest.TestCase):
    def setUp(self):
        models.clear_cache()

    def tearDown(self):
        models.clear_cache()

    def test_summarize_calls_summarizer(self):
        def transport(url, payload, api_key):
            self.assertEqual(payload["model"], SUMMARIZER.slug)
            return _reply("2 of 3 tasks succeeded.")
        orch = _orch("k", transport=transport)
        out = orch.summarize([{"label": "a", "status": "done"}])
        self.assertEqual(out, "2 of 3 tasks succeeded.")


class TransportErrorTests(unittest.TestCase):
    def setUp(self):
        models.clear_cache()

    def tearDown(self):
        models.clear_cache()

    def test_transport_raising_propagates(self):
        def boom(url, payload, api_key):
            raise OrchestratorError("network down")
        orch = _orch("k", transport=boom)
        with self.assertRaises(OrchestratorError):
            orch.plan("anything")

    def test_unexpected_response_shape_raises(self):
        def weird(url, payload, api_key):
            return {"nope": True}
        orch = _orch("k", transport=weird)
        with self.assertRaises(OrchestratorError):
            orch.plan("anything")


if __name__ == "__main__":
    unittest.main()
