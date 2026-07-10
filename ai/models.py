"""
OpenRouter model roster for the V4.0 AI assistant.

Verified against https://openrouter.ai/api/v1/models on 2026-07-03 — all four
slugs exist and are free (prompt/completion pricing = 0).

The assistant uses these four free models cooperatively (multi-model
orchestration): a strong planner drafts the batch plan, a mid model turns it
into concrete commands, a checker validates it, and a small fast model
summarizes results / logs. Any operation that touches the filesystem is only
executed AFTER the user confirms the plan (decision D4).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    slug: str          # OpenRouter model id
    role: str          # role in the collaboration
    context: int       # context window (tokens)


# Default free-model roster (verified 2026-07-03).
PLANNER = Model("openai/gpt-oss-120b:free", "planner", 131_072)
EXECUTOR = Model("google/gemma-4-31b-it:free", "executor", 262_144)
CHECKER = Model("google/gemma-4-26b-a4b-it:free", "checker", 262_144)
SUMMARIZER = Model("liquid/lfm-2.5-1.2b-thinking:free", "summarizer", 32_768)

ROSTER: list[Model] = [PLANNER, EXECUTOR, CHECKER, SUMMARIZER]

# OpenRouter endpoint. The user's own API key is supplied at runtime and is
# stored ONLY in the Tauri secure layer — never hard-coded, never committed.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# NOTE: free-tier rate limits are account-level (not per-model): roughly
# 20 req/min, daily cap depends on whether the account holds >=10 credits
# (~50/day if not, ~1000/day if so). Verify on the user's dashboard.
