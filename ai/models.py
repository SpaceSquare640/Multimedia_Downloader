"""
OpenRouter model roster for the V4.0 AI assistant.

Verified against https://openrouter.ai/api/v1/models on 2026-07-17 — all four
slugs exist and are free (prompt/completion pricing = 0).

The assistant uses these four free models cooperatively (multi-model
orchestration): a strong planner drafts the batch plan, a mid model turns it
into concrete commands, a checker validates it, and a small fast model
summarizes results / logs. Any operation that touches the filesystem is only
executed AFTER the user confirms the plan (decision D4).

⚠️ OpenRouter free slugs churn fast (only ~20 ``:free`` models exist at any
time). The original PLANNER ``openai/gpt-oss-120b:free`` and SUMMARIZER
``liquid/lfm-2.5-1.2b-thinking:free`` (verified 2026-07-03) were BOTH delisted
by 2026-07-17 — that was the V4.0 AI-assistant runtime error (planner is the
first call in ``Orchestrator.plan()``, so a dead slug → HTTP 404 → error).
Re-check any ``:free`` slug against ``/api/v1/models`` (public, no key needed)
before trusting it. Future hardening: validate the roster at startup / fall
back to a live free model automatically.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    slug: str          # OpenRouter model id
    role: str          # role in the collaboration
    context: int       # context window (tokens)


# Default free-model roster (verified 2026-07-17).
PLANNER = Model("meta-llama/llama-3.3-70b-instruct:free", "planner", 131_072)
EXECUTOR = Model("google/gemma-4-31b-it:free", "executor", 262_144)
CHECKER = Model("google/gemma-4-26b-a4b-it:free", "checker", 262_144)
SUMMARIZER = Model("meta-llama/llama-3.2-3b-instruct:free", "summarizer", 131_072)

ROSTER: list[Model] = [PLANNER, EXECUTOR, CHECKER, SUMMARIZER]

# OpenRouter endpoint. The user's own API key is supplied at runtime and is
# stored ONLY in the Tauri secure layer — never hard-coded, never committed.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# NOTE: free-tier rate limits are account-level (not per-model): roughly
# 20 req/min, daily cap depends on whether the account holds >=10 credits
# (~50/day if not, ~1000/day if so). Verify on the user's dashboard.
