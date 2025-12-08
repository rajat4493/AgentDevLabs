"""
Provider registry for the router.

Each adapter module must expose `plan(...)` and `execute(...)`.
"""

from __future__ import annotations

from . import ollama_adapter
from . import stub
from .anthropic_adapter import anthropic_adapter
from .gemini_adapter import gemini_adapter

try:
    from . import openai_adapter
except ImportError:  # pragma: no cover - optional dependency guard
    openai_adapter = None  # type: ignore

PROVIDERS = {
    "ollama": ollama_adapter,
    "anthropic": anthropic_adapter,
    "gemini": gemini_adapter,
    "stub": stub,
}

if openai_adapter is not None:
    PROVIDERS["openai"] = openai_adapter

__all__ = ["PROVIDERS"]
