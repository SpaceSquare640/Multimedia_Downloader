"""
OpenRouter model roster for the AI assistant.

The assistant uses four free models cooperatively (multi-model orchestration):
a strong planner drafts the batch plan, a mid model turns it into concrete
commands, a checker validates it, and a small fast model summarizes results /
logs. Any operation that touches the filesystem is only executed AFTER the
user confirms the plan (decision D4).

⚠️ OpenRouter free slugs churn fast (only ~20 ``:free`` models exist at any
time). Two rounds of this are on record: the V4.0 PLANNER
``openai/gpt-oss-120b:free`` and SUMMARIZER ``liquid/lfm-2.5-1.2b-thinking:free``
were delisted within two weeks (that was the V4.0 AI-assistant runtime error —
the planner is the first call in ``Orchestrator.plan()``, so a dead slug → HTTP
404 → the whole pipeline fails); their V4.1 replacements
``meta-llama/llama-3.3-70b-instruct:free`` and
``meta-llama/llama-3.2-3b-instruct:free`` were gone by 2026-09-13 in turn.

The constants below are therefore only a **starting point**, not a promise.
:func:`resolve_roster` checks them against the live catalogue
(``GET /api/v1/models``, public — no API key needed) and substitutes a live
free model for any slug that has been delisted.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass(frozen=True)
class Model:
    slug: str          # OpenRouter model id
    role: str          # role in the collaboration
    context: int       # context window (tokens)


# Default free-model roster (verified against the live catalogue 2026-09-13).
# Treated as preferences that resolve_roster() may override — never as
# guaranteed-live slugs. Both meta-llama entries here before 2026-09-13 had
# already been delisted again, which is why the resolver exists; refreshing
# these constants only saves the resolver a detour, it is not a fix in itself.
PLANNER = Model("nvidia/nemotron-3-ultra-550b-a55b:free", "planner", 1_000_000)
EXECUTOR = Model("google/gemma-4-31b-it:free", "executor", 262_144)
CHECKER = Model("google/gemma-4-26b-a4b-it:free", "checker", 262_144)
SUMMARIZER = Model("liquid/lfm-2.5-2.6b:free", "summarizer", 65_536)

ROSTER: list[Model] = [PLANNER, EXECUTOR, CHECKER, SUMMARIZER]

# OpenRouter endpoint. The user's own API key is supplied at runtime and is
# stored ONLY in the Tauri secure layer — never hard-coded, never committed.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# NOTE: free-tier rate limits are account-level (not per-model): roughly
# 20 req/min, daily cap depends on whether the account holds >=10 credits
# (~50/day if not, ~1000/day if so). Verify on the user's dashboard.

#: ``() -> list[model_dict]`` — injectable for tests; no API key required.
CatalogFetch = Callable[[], list[dict]]

#: How long a successful catalogue lookup is reused. One plan() makes four
#: model calls; without this they would each re-fetch. Six hours sits well
#: inside the timescale on which OpenRouter's free tier churns.
CATALOG_TTL_S = 6 * 60 * 60

#: Alternates kept per role for the call-time fallback (see
#: ``Orchestrator._call``) — the catalogue can lag reality by minutes.
_MAX_ALTERNATES = 3


# ─────────────────────────────────────────────────────────────────────────────
#  Live catalogue
# ─────────────────────────────────────────────────────────────────────────────

def _default_catalog_fetch() -> list[dict]:
    """Fetch the public model catalogue. Raises on any network/parse failure."""
    # noqa justification: the URL is built from OPENROUTER_BASE_URL, a module
    # constant pinned to https -- never from user input, so the file:/custom-
    # scheme risk this rule guards against cannot arise here.
    req = urllib.request.Request(  # noqa: S310
        f"{OPENROUTER_BASE_URL}/models",
        headers={"Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        doc = json.loads(resp.read().decode("utf-8"))
    data = doc.get("data")
    if not isinstance(data, list):
        raise ValueError("catalogue reply had no 'data' list")
    return data


def _price(value) -> Optional[float]:
    """
    Parse one OpenRouter pricing field.

    The API has shipped these as both numbers and decimal strings ("0",
    "0.0000001"), so parse leniently — but return ``None`` (not 0.0) for
    anything unparseable, so an unknown price is never mistaken for free.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_free(entry: dict) -> bool:
    """True only when prompt AND completion are known to cost zero."""
    pricing = entry.get("pricing")
    if not isinstance(pricing, dict):
        return False
    prompt = _price(pricing.get("prompt"))
    completion = _price(pricing.get("completion"))
    return prompt == 0.0 and completion == 0.0


def _family(slug: str) -> str:
    """Vendor prefix — ``meta-llama/llama-3.3-70b:free`` → ``meta-llama``."""
    return slug.split("/", 1)[0] if "/" in slug else slug


#: Free-tier listings include models that are not general chat models —
#: safety/moderation classifiers, embedding and re-ranking models, image or
#: speech endpoints. They answer the API but cannot draft or refine a plan, so
#: they must never be chosen as a substitute. (Observed for real: a dead
#: planner once resolved to `nvidia/...-content-safety:free`, whose replies are
#: safety labels, not JSON plans.)
_NON_CHAT_MARKERS = (
    "content-safety", "guard", "moderation", "safety",
    "embed", "rerank", "reranker",
    "whisper", "tts", "stt", "transcribe",
    "image", "vision-encoder", "diffusion",
)


def _is_chat_model(slug: str, entry: Optional[dict] = None) -> bool:
    """
    Whether a catalogue entry is a general text-in/text-out chat model.

    Two independent checks, because neither alone is enough:

    * declared modality — catches image/audio generators (a music model lists
      ``text+image->text+audio``) that the name alone would not betray;
    * name markers — catches models that *are* text->text but answer something
      other than the question, e.g. a content-safety classifier returning a
      safety label where a JSON plan was asked for.
    """
    if entry is not None:
        arch = entry.get("architecture")
        if isinstance(arch, dict):
            outputs = arch.get("output_modalities")
            inputs = arch.get("input_modalities")
            if isinstance(outputs, list) and outputs:
                # Must produce text, and only text.
                if "text" not in outputs or len(set(outputs) - {"text"}) > 0:
                    return False
            if isinstance(inputs, list) and inputs and "text" not in inputs:
                return False

    lowered = slug.lower()
    return not any(marker in lowered for marker in _NON_CHAT_MARKERS)


def _free_models(entries: list[dict]) -> list[Model]:
    """Map raw catalogue entries to the free chat models we could actually use."""
    out: list[Model] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        slug = e.get("id")
        if not isinstance(slug, str) or not slug or not _is_free(e):
            continue
        if not _is_chat_model(slug, e):
            continue
        ctx = e.get("context_length")
        out.append(Model(slug, "", ctx if isinstance(ctx, int) and ctx > 0 else 0))
    return out


def _rank_for(preferred: Model, candidates: list[Model]) -> list[Model]:
    """
    Order substitutes for ``preferred``, best first.

    Same vendor family first (a llama-shaped prompt tends to keep working on
    another llama), then the closest context window to what the role was tuned
    for, then slug order — the last key only to break ties deterministically,
    so the same catalogue always yields the same choice.
    """
    fam = _family(preferred.slug)
    return sorted(
        candidates,
        key=lambda m: (0 if _family(m.slug) == fam else 1,
                       abs(m.context - preferred.context),
                       m.slug),
    )


@dataclass
class Roster:
    """
    The models :class:`~ai.orchestrator.Orchestrator` should actually call.

    ``verified`` is False when the catalogue could not be read — the defaults
    are then used as-is (fail open: a catalogue blip must not disable a feature
    that might well still work).
    """
    models: dict[str, Model]
    alternates: dict[str, list[Model]] = field(default_factory=dict)
    #: Human-readable notes about substitutions / verification failure.
    #: Surfaced to the user through the plan's ``warnings`` list.
    notes: list[str] = field(default_factory=list)
    verified: bool = True

    def get(self, role: str) -> Model:
        return self.models[role]

    def next_alternate(self, role: str, exclude: set[str]) -> Optional[Model]:
        """First alternate for ``role`` whose slug isn't in ``exclude``."""
        for m in self.alternates.get(role, []):
            if m.slug not in exclude:
                return m
        return None


def _defaults_roster(notes: list[str], verified: bool) -> Roster:
    return Roster(models={m.role: m for m in ROSTER}, notes=notes, verified=verified)


# Module-level TTL cache: (expires_at, Roster).
_cache: Optional[tuple[float, Roster]] = None


def clear_cache() -> None:
    """Drop the cached catalogue lookup (tests / long-lived processes)."""
    global _cache
    _cache = None


def resolve_roster(
    fetch: Optional[CatalogFetch] = None,
    use_cache: bool = True,
    now: Optional[Callable[[], float]] = None,
) -> Roster:
    """
    Return the roster to use, substituting live free models for dead slugs.

    Never raises: if the catalogue can't be read the hard-coded defaults come
    back with ``verified=False``, because a failed lookup is not evidence that
    a slug is dead.
    """
    global _cache
    clock = now or time.monotonic
    if use_cache and _cache and _cache[0] > clock():
        return _cache[1]

    try:
        entries = (fetch or _default_catalog_fetch)()
        candidates = _free_models(entries)
        if not candidates:
            raise ValueError("catalogue listed no free models")
    except Exception as e:
        # Fail open — see the docstring.
        return _defaults_roster([f"could not verify AI model roster: {e}"], verified=False)

    live = {m.slug for m in candidates}
    models: dict[str, Model] = {}
    alternates: dict[str, list[Model]] = {}
    notes: list[str] = []

    for preferred in ROSTER:
        ranked = _rank_for(preferred, [m for m in candidates if m.slug != preferred.slug])
        if preferred.slug in live:
            models[preferred.role] = preferred
            alternates[preferred.role] = [
                Model(m.slug, preferred.role, m.context) for m in ranked[:_MAX_ALTERNATES]
            ]
            continue
        if ranked:
            sub = ranked[0]
            models[preferred.role] = Model(sub.slug, preferred.role, sub.context)
            alternates[preferred.role] = [
                Model(m.slug, preferred.role, m.context)
                for m in ranked[1:_MAX_ALTERNATES + 1]
            ]
            notes.append(
                f"{preferred.role}: {preferred.slug} is no longer available — "
                f"using {sub.slug} instead"
            )
        else:
            models[preferred.role] = preferred
            alternates[preferred.role] = []
            notes.append(f"{preferred.role}: {preferred.slug} looks unavailable and "
                         "no free substitute was found")

    roster = Roster(models=models, alternates=alternates, notes=notes, verified=True)
    if use_cache:
        _cache = (clock() + CATALOG_TTL_S, roster)
    return roster
