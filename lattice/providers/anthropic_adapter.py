from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    import anthropic
    from anthropic import Anthropic
except ImportError:  # pragma: no cover - optional dependency
    anthropic = None  # type: ignore
    Anthropic = None  # type: ignore

if anthropic is not None:  # pragma: no cover - type guard
    AnthropicRateLimitError = getattr(anthropic, "RateLimitError", Exception)
    AnthropicAPITimeoutError = getattr(anthropic, "APITimeoutError", Exception)
    AnthropicAPIStatusError = getattr(anthropic, "APIStatusError", Exception)
    AnthropicAPIError = getattr(anthropic, "APIError", Exception)
else:  # pragma: no cover
    AnthropicRateLimitError = Exception
    AnthropicAPITimeoutError = Exception
    AnthropicAPIStatusError = Exception
    AnthropicAPIError = Exception

from ..config import settings
from ..errors import (
    ConfigurationError,
    ProviderInternalError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from ..logging import configure_logger, log_event

logger = configure_logger("lattice.providers.anthropic")

DEFAULT_MODEL = "claude-3-sonnet-20240229"
DEFAULT_MAX_TOKENS = 1024

ANTHROPIC_PRICING: Dict[str, Dict[str, float]] = {
    # USD cost per single token
    "claude-3-opus-20240229": {"input": 15.0 / 1_000_000, "output": 75.0 / 1_000_000},
    "claude-3-sonnet-20240229": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
    "claude-3-haiku-20240307": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
}

MODEL_ALIASES = {
    "claude-3-haiku": "claude-3-haiku-20240307",
}


def _resolve_model_name(model: str | None) -> str:
    name = (model or DEFAULT_MODEL).strip()
    lower = name.lower()
    return MODEL_ALIASES.get(lower, name)


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = ANTHROPIC_PRICING.get(model) or ANTHROPIC_PRICING[DEFAULT_MODEL]
    cost_input = prompt_tokens * pricing["input"]
    cost_output = completion_tokens * pricing["output"]
    return round(cost_input + cost_output, 8)


class AnthropicProvider:
    def __init__(self) -> None:
        self._client: Anthropic | None = None

    def _ensure_client(self) -> Anthropic:
        if Anthropic is None:
            raise ConfigurationError("anthropic package is not installed. Add it to requirements.", provider="anthropic")
        if self._client is None:
            api_key = settings.anthropic_api_key
            if not api_key:
                raise ConfigurationError("ANTHROPIC_API_KEY is not configured", provider="anthropic")
            self._client = Anthropic(api_key=api_key)
        return self._client

    @staticmethod
    def _format_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        formatted: List[Dict[str, str]] = []
        for msg in messages:
            role = msg.get("role")
            content = (msg.get("content") or "").strip()
            if not role or not content:
                continue
            if role not in {"user", "assistant"}:
                continue
            formatted.append({"role": role, "content": content})
        if not formatted:
            formatted.append({"role": "user", "content": ""})
        return formatted

    def plan(self, run_payload: Dict[str, Any], model_name: str = DEFAULT_MODEL) -> Dict[str, Any]:
        params = run_payload or {}
        temperature = params.get("temperature")
        if not isinstance(temperature, (int, float)):
            temperature = 0.2

        max_tokens = params.get("max_tokens", DEFAULT_MAX_TOKENS)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            max_tokens = DEFAULT_MAX_TOKENS

        system_prompt = params.get("system_prompt") or settings.anthropic_system_prompt

        return {
            "target": {"provider": "anthropic", "model": model_name},
            "params": {
                "temperature": float(temperature),
                "max_tokens": max_tokens,
                "system_prompt": system_prompt,
            },
        }

    def execute(self, plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        target = plan.get("target") or {}
        params = plan.get("params") or {}

        requested_model = target.get("model") or DEFAULT_MODEL
        model = _resolve_model_name(requested_model)
        max_tokens = int(params.get("max_tokens") or DEFAULT_MAX_TOKENS)
        temperature = float(params.get("temperature", 0.2))
        system_prompt = params.get("system_prompt") or settings.anthropic_system_prompt

        payload_messages = [{"role": "user", "content": prompt}]
        latency_ms = 0.0
        prompt_tokens = 0
        completion_tokens = 0
        text_output = ""

        resp = self.chat(
            model=model,
            messages=payload_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
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
            provider="anthropic",
            model=model,
            latency_ms=int(latency_ms),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
        )

        return {
            "output": text_output,
            "confidence": 0.92,
            "latency_ms": int(latency_ms),
            "cost_usd": cost_usd,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "provenance": {
                "provider": "anthropic",
                "model": model,
                "mode": "messages.create",
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
            },
        }

    def chat(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        system: str | None = None,
    ) -> Dict[str, Any]:
        client = self._ensure_client()
        formatted_messages = self._format_messages(messages)
        kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system

        t0 = time.perf_counter()
        try:
            resp = client.messages.create(**kwargs)
        except AnthropicRateLimitError as exc:
            log_event(logger, logging.WARNING, "provider_rate_limit", provider="anthropic")
            raise ProviderRateLimitError("Anthropic rate limit exceeded.", provider="anthropic") from exc
        except AnthropicAPITimeoutError as exc:
            log_event(logger, logging.WARNING, "provider_timeout", provider="anthropic")
            raise ProviderTimeoutError("Anthropic did not respond in time.", provider="anthropic") from exc
        except AnthropicAPIStatusError as exc:
            status_code = getattr(exc, "status_code", 500)
            if 400 <= status_code < 500:
                log_event(logger, logging.WARNING, "provider_validation_error", provider="anthropic", status=status_code)
                raise ProviderValidationError("Anthropic rejected the request.", provider="anthropic") from exc
            log_event(logger, logging.ERROR, "provider_internal_error", provider="anthropic", status=status_code)
            raise ProviderInternalError("Anthropic upstream error.", provider="anthropic") from exc
        except AnthropicAPIError as exc:
            log_event(logger, logging.ERROR, "provider_api_error", provider="anthropic")
            raise ProviderInternalError("Anthropic API error.", provider="anthropic") from exc
        except Exception as exc:  # pragma: no cover - defensive
            log_event(logger, logging.ERROR, "provider_internal_error", provider="anthropic")
            raise ProviderInternalError("Anthropic call failed.", provider="anthropic") from exc
        latency_ms = (time.perf_counter() - t0) * 1000.0

        content_blocks = resp.content or []
        text = ""
        if content_blocks:
            text = getattr(content_blocks[0], "text", "") or ""

        usage = getattr(resp, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "output_tokens", 0) if usage else 0

        return {
            "content": text,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
            "latency_ms": latency_ms,
        }


anthropic_adapter = AnthropicProvider()
