"""
Tests for the live-catalogue roster resolution (ai/models.py).

The hard-coded `:free` slugs go stale — OpenRouter delisted two of them between
2026-07-03 and 2026-07-17, which is what broke the V4.0 AI assistant at
runtime. These tests pin the substitution behaviour that replaced that failure
mode. Everything here is offline: the catalogue fetch is injected.
"""
from __future__ import annotations

import unittest

import _path  # noqa: F401  — puts the project root on sys.path

from ai import models
from ai.models import PLANNER, ROSTER, Model, resolve_roster


def entry(slug: str, ctx: int = 131_072, prompt="0", completion="0") -> dict:
    return {"id": slug, "context_length": ctx,
            "pricing": {"prompt": prompt, "completion": completion}}


def catalogue(*entries: dict):
    """Build an injectable fetch returning these catalogue entries."""
    return lambda: list(entries)


def all_live() -> list[dict]:
    """Every default slug present and free."""
    return [entry(m.slug, m.context) for m in ROSTER]


def _family_of(slug: str) -> str:
    return slug.split("/", 1)[0]


#: The planner's vendor prefix, derived rather than written out: these tests
#: pin ranking behaviour, not whichever slug the roster currently prefers.
PLANNER_FAMILY = _family_of(PLANNER.slug)


def sibling(name: str, ctx: int) -> dict:
    """A same-vendor candidate for the planner role."""
    return entry(f"{PLANNER_FAMILY}/{name}:free", ctx)


def without_planner_family() -> list[dict]:
    """
    A catalogue holding no entry from the planner's own vendor.

    The planner's substitution tests need a blank slate: another default may
    share the planner's family and context window, and would then (correctly)
    win every ranking, masking what is under test.
    """
    return [entry(m.slug, m.context) for m in ROSTER
            if _family_of(m.slug) != PLANNER_FAMILY]


class PricingTests(unittest.TestCase):
    def test_string_and_numeric_zero_both_count_as_free(self):
        self.assertTrue(models._is_free({"pricing": {"prompt": "0", "completion": 0}}))

    def test_nonzero_price_is_not_free(self):
        self.assertFalse(models._is_free({"pricing": {"prompt": "0.0000001", "completion": "0"}}))

    def test_unparseable_price_is_not_free(self):
        # An unknown price must never be mistaken for free.
        self.assertFalse(models._is_free({"pricing": {"prompt": None, "completion": "0"}}))

    def test_missing_pricing_is_not_free(self):
        self.assertFalse(models._is_free({"id": "x/y"}))


class ResolveRosterTests(unittest.TestCase):
    def setUp(self):
        models.clear_cache()

    def tearDown(self):
        models.clear_cache()

    def test_all_slugs_live_means_no_substitution(self):
        r = resolve_roster(fetch=catalogue(*all_live()), use_cache=False)
        self.assertTrue(r.verified)
        self.assertEqual(r.notes, [])
        self.assertEqual(r.get("planner").slug, PLANNER.slug)

    def test_dead_planner_is_substituted(self):
        live = without_planner_family()
        live.append(sibling("sibling-model", PLANNER.context))
        r = resolve_roster(fetch=catalogue(*live), use_cache=False)
        self.assertNotEqual(r.get("planner").slug, PLANNER.slug)
        self.assertEqual(r.get("planner").role, "planner")
        planner_notes = [n for n in r.notes if n.startswith("planner:")]
        self.assertEqual(len(planner_notes), 1)
        self.assertIn(PLANNER.slug, planner_notes[0])

    def test_same_family_preferred_over_closer_context(self):
        # An exact context match from another vendor must still lose to the
        # same-vendor candidate: prompt compatibility outranks window size.
        live = without_planner_family()
        live.append(entry("other/exact-context:free", PLANNER.context))
        live.append(sibling("wider-window", PLANNER.context * 2))
        r = resolve_roster(fetch=catalogue(*live), use_cache=False)
        self.assertEqual(r.get("planner").slug, f"{PLANNER_FAMILY}/wider-window:free")

    def test_closest_context_wins_within_same_family(self):
        live = without_planner_family()
        live.append(sibling("far", PLANNER.context * 8))
        live.append(sibling("near", PLANNER.context + 1_000))
        r = resolve_roster(fetch=catalogue(*live), use_cache=False)
        self.assertEqual(r.get("planner").slug, f"{PLANNER_FAMILY}/near:free")

    def test_substitution_is_deterministic_on_ties(self):
        live = without_planner_family()
        live.append(entry("zeta/tie:free", PLANNER.context))
        live.append(entry("alpha/tie:free", PLANNER.context))
        picks = {
            resolve_roster(fetch=catalogue(*live), use_cache=False).get("planner").slug
            for _ in range(5)
        }
        self.assertEqual(picks, {"alpha/tie:free"})

    def test_paid_models_are_never_chosen(self):
        # Only two candidates, and the paid one is the perfect contextual match
        # — it must still be passed over, or a "free models only" assistant
        # would quietly start billing the user's account.
        r = resolve_roster(use_cache=False, fetch=catalogue(
            entry("paid/expensive", PLANNER.context, prompt="0.001", completion="0.002"),
            entry("free/cheap:free", PLANNER.context * 4),
        ))
        for role in ("planner", "executor", "checker", "summarizer"):
            self.assertEqual(r.get(role).slug, "free/cheap:free")

    def test_non_chat_models_are_never_chosen(self):
        # Seen in the real catalogue: with no same-vendor chat model left, the
        # planner resolved to a content-safety classifier, which answers the
        # API but returns safety labels instead of a JSON plan.
        r = resolve_roster(use_cache=False, fetch=catalogue(
            entry("nvidia/nemotron-3.5-content-safety:free", PLANNER.context),
            entry("some/embed-v2:free", PLANNER.context),
            entry("usable/chat-model:free", PLANNER.context * 3),
        ))
        self.assertEqual(r.get("planner").slug, "usable/chat-model:free")
        self.assertNotIn("nvidia/nemotron-3.5-content-safety:free",
                         [m.slug for m in r.alternates["planner"]])

    def test_non_text_output_models_are_never_chosen(self):
        # A music model lists `text+image->text+audio` and carries nothing in
        # its name to give it away — only the declared modality catches it.
        music = entry("google/lyria-3-pro-preview", PLANNER.context)
        music["architecture"] = {"input_modalities": ["text", "image"],
                                 "output_modalities": ["text", "audio"]}
        chat = entry("usable/chat-model:free", PLANNER.context * 3)
        chat["architecture"] = {"input_modalities": ["text"],
                                "output_modalities": ["text"]}
        r = resolve_roster(use_cache=False, fetch=catalogue(music, chat))
        self.assertEqual(r.get("planner").slug, "usable/chat-model:free")

    def test_entries_without_architecture_still_usable(self):
        # The modality check must be additive: an entry that simply omits
        # `architecture` is judged on its name alone, not discarded.
        r = resolve_roster(use_cache=False,
                           fetch=catalogue(entry("plain/model:free", PLANNER.context)))
        self.assertEqual(r.get("planner").slug, "plain/model:free")

    def test_catalogue_failure_falls_back_to_defaults_unverified(self):
        def boom():
            raise OSError("network down")
        r = resolve_roster(fetch=boom, use_cache=False)
        self.assertFalse(r.verified)
        self.assertEqual(r.get("planner").slug, PLANNER.slug)
        self.assertTrue(r.notes and "network down" in r.notes[0])

    def test_empty_catalogue_falls_back_to_defaults(self):
        r = resolve_roster(fetch=catalogue(), use_cache=False)
        self.assertFalse(r.verified)
        self.assertEqual(r.get("summarizer").slug, models.SUMMARIZER.slug)

    def test_malformed_entries_are_skipped_not_fatal(self):
        live = all_live() + ["not a dict", {"no_id": True}, {"id": 42}]
        r = resolve_roster(fetch=catalogue(*live), use_cache=False)
        self.assertTrue(r.verified)
        self.assertEqual(r.notes, [])

    def test_cache_reuses_one_lookup(self):
        calls = []

        def counting():
            calls.append(1)
            return all_live()

        resolve_roster(fetch=counting, now=lambda: 0.0)
        resolve_roster(fetch=counting, now=lambda: 1.0)
        self.assertEqual(len(calls), 1)

    def test_cache_expires_after_ttl(self):
        calls = []

        def counting():
            calls.append(1)
            return all_live()

        resolve_roster(fetch=counting, now=lambda: 0.0)
        resolve_roster(fetch=counting, now=lambda: models.CATALOG_TTL_S + 1.0)
        self.assertEqual(len(calls), 2)


class AlternatesTests(unittest.TestCase):
    def setUp(self):
        models.clear_cache()

    def tearDown(self):
        models.clear_cache()

    def test_alternates_exclude_already_tried(self):
        live = all_live() + [sibling("alt-a", PLANNER.context),
                             sibling("alt-b", PLANNER.context)]
        r = resolve_roster(fetch=catalogue(*live), use_cache=False)
        first = r.next_alternate("planner", set())
        self.assertIsNotNone(first)
        second = r.next_alternate("planner", {first.slug})
        self.assertNotEqual(second.slug, first.slug)

    def test_next_alternate_returns_none_when_exhausted(self):
        r = resolve_roster(fetch=catalogue(*all_live()), use_cache=False)
        tried = {m.slug for m in r.alternates["planner"]}
        self.assertIsNone(r.next_alternate("planner", tried))

    def test_alternates_carry_the_role(self):
        r = resolve_roster(fetch=catalogue(*all_live()), use_cache=False)
        for m in r.alternates["checker"]:
            self.assertEqual(m.role, "checker")
        self.assertIsInstance(r.get("checker"), Model)


if __name__ == "__main__":
    unittest.main()
