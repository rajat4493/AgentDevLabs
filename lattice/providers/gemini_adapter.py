from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    import google.generativeai as genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None  # type: ignore

from ..config import settings
from ..errors import (
    ConfigurationError,
    ProviderInternalError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from ..logging import configure_logger, log_event

logger = configure_logger("lattice.providers.gemini")

DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_MAX_TOKENS = 1024

GEMINI_PRICING: Dict[str, Dict[str, float]] = {
    # USD cost per token
    "gemini-2.0-flash": {"input": 0.25 / 1_000_000, "output": 0.5 / 1_000_000},
    "gemini-1.5-flash": {"input": 0.35 / 1_000_000, "output": 1.05 / 1_000_000},
    "gemini-1.5-pro": {"input": 7.0 / 1_000_000, "output": 21.0 / 1_000_000},
}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = GEMINI_PRICING.get(model) or GEMINI_PRICING[DEFAULT_MODEL]
    cost_input = prompt_tokens * pricing["input"]
    cost_output = completion_tokens * pricing["output"]
    return round(cost_input + cost_output, 8)


class GeminiProvider:
    def __init__(self) -> None:
        self._configured = False

    def _ensure_configured(self) -> None:
        if genai is None:
            raise ConfigurationError("google-generativeai is not installed. Add it to requirements.", provider="gemini")
        if not self._configured:
            api_key = settings.gemini_api_key
            if not api_key:
                raise ConfigurationError("GEMINI_API_KEY is not configured", provider="gemini")
            genai.configure(api_key=api_key)
            self._configured = True

    @staticmethod
    def _collapse_messages(messages: List[Dict[str, Any]]) -> str:
        user_chunks: List[str] = []
        for msg in messages:
            role = msg.get("role")
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            if role == "user":
                user_chunks.append(content)
            # Gemini chat currently ignores assistant history for router use-case
        return "\n".join(user_chunks).strip()

    def plan(self, run_payload: Dict[str, Any], model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
        params = run_payload or {}
        temperature = params.get("temperature")
        if not isinstance(temperature, (int, float)):
            temperature = 0.3

        max_tokens = params.get("max_tokens", DEFAULT_MAX_TOKENS)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            max_tokens = DEFAULT_MAX_TOKENS

        return {
            "target": {"provider": "gemini", "model": model_name},
            "params": {
                "temperature": float(temperature),
                "max_tokens": max_tokens,
            },
        }

    def execute(self, plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        target = plan.get("target") or {}
        params = plan.get("params") or {}

        model = target.get("model") or DEFAULT_MODEL
        max_tokens = int(params.get("max_tokens") or DEFAULT_MAX_TOKENS)
        temperature = float(params.get("temperature", 0.3))

        resp = self.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text_output = resp["content"].strip()
        latency_ms = resp["latency_ms"]
        usage = resp.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))

        cost_usd = _estimate_cost(model, prompt_tokens, completion_tokens)

        log_event(
            logger,
            logging.INFO,
            "provider_success",
            provider="gemini",
            model=model,
            latency_ms=resp["latency_ms"],
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
        )

        return {
            "output": text_output,
            "confidence": 0.88,
            "latency_ms": int(latency_ms),
            "cost_usd": cost_usd,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "provenance": {
                "provider": "gemini",
                "model": model,
                "mode": "generate_content",
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
            },
        }

    def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: float = 0.3,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Dict[str, Any]:
        self._ensure_configured()
        user_text = self._collapse_messages(messages) or ""

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        gen_model = genai.GenerativeModel(model)

        t0 = time.perf_counter()
        try:
            resp = gen_model.generate_content(
                user_text,
                generation_config=generation_config,
            )
        except Exception as exc:  # pragma: no cover - upstream errors
            status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            try:
                status_int = int(status_code) if status_code is not None else None
            except (TypeError, ValueError):
                status_int = None
            message = str(exc).lower()
            if status_int == 429:
                log_event(logger, logging.WARNING, "provider_rate_limit", provider="gemini")
                raise ProviderRateLimitError("Gemini rate limit exceeded.", provider="gemini") from exc
            if status_int is not None and 400 <= status_int < 500:
                log_event(logger, logging.WARNING, "provider_validation_error", provider="gemini", status=status_int)
                raise ProviderValidationError("Gemini rejected the request.", provider="gemini") from exc
            if "timeout" in message:
                log_event(logger, logging.WARNING, "provider_timeout", provider="gemini")
                raise ProviderTimeoutError("Gemini request timed out.", provider="gemini") from exc
            log_event(logger, logging.ERROR, "provider_internal_error", provider="gemini")
            raise ProviderInternalError("Gemini call failed.", provider="gemini") from exc
        latency_ms = (time.perf_counter() - t0) * 1000.0

        text = getattr(resp, "text", "") or ""
        usage = getattr(resp, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        return {
            "content": text,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
            "latency_ms": latency_ms,
        }


gemini_adapter = GeminiProvider()
