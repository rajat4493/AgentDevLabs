from __future__ import annotations

import os
import time
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    import google.generativeai as genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None  # type: ignore

DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_MAX_TOKENS = 1024

GEMINI_PRICING: Dict[str, Dict[str, float]] = {
    # USD cost per token
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
            raise RuntimeError("google-generativeai is not installed. Add it to requirements.")
        if not self._configured:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY is not configured")
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

        latency_ms = 0.0
        prompt_tokens = 0
        completion_tokens = 0
        text_output = ""

        try:
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
        except Exception as exc:  # pragma: no cover - safety net
            text_output = f"[Gemini error] {exc}"

        cost_usd = _estimate_cost(model, prompt_tokens, completion_tokens)

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
        resp = gen_model.generate_content(
            user_text,
            generation_config=generation_config,
        )
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
