"""
V4.0 AI assistant package.

- models.py       : verified OpenRouter free-model roster + roles
- orchestrator.py : multi-model collaboration (planner -> executor -> guard
                    -> checker). Produces a plan; execution happens only
                    after the user confirms (decision D4).
"""

from __future__ import annotations

from .models import CHECKER, EXECUTOR, OPENROUTER_BASE_URL, PLANNER, ROSTER, SUMMARIZER, Model
from .orchestrator import Orchestrator, OrchestratorError

__all__ = [
    "Model", "PLANNER", "EXECUTOR", "CHECKER", "SUMMARIZER", "ROSTER",
    "OPENROUTER_BASE_URL",
    "Orchestrator", "OrchestratorError",
]
