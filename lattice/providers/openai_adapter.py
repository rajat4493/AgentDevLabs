import logging
import time
from typing import Any, Dict

import requests

from ..cost import compute_costs
from ..config import settings
from ..errors import (
    ConfigurationError,
    ProviderInternalError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from ..logging import configure_logger, log_event

logger = configure_logger("lattice.providers.openai")


def plan(run_payload: Dict[str, Any], model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    temperature = run_payload.get("temperature") if isinstance(run_payload, dict) else None
    if not isinstance(temperature, (int, float)):
        temperature = 0.2

    max_tokens = run_payload.get("max_tokens", 512) if isinstance(run_payload, dict) else 512
    if not isinstance(max_tokens, int):
        max_tokens = 512

    return {
        "target": {
            "provider": "openai",
            "model": model_name,
        },
        "params": {
            "temperature": float(temperature),
            "max_tokens": max_tokens,
        },
    }


def execute(plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    target = plan.get("target") or {}
    params = plan.get("params") or {}

    model = target.get("model") or "gpt-4o-mini"
    temperature = params.get("temperature", 0.2)
    max_tokens = params.get("max_tokens", 512)

    api_key = settings.openai_api_key
    if not api_key:
        raise ConfigurationError("OPENAI_API_KEY is not configured", provider="openai")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise assistant running inside the lattice router.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    t0 = time.perf_counter()
    try:
        resp = requests.post(
            settings.openai_api_base.rstrip("/") + "/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
    except requests.Timeout as exc:
        log_event(logger, logging.WARNING, "provider_timeout", provider="openai")
        raise ProviderTimeoutError("OpenAI did not respond within 60 seconds.", provider="openai") from exc
    except requests.RequestException as exc:
        log_event(logger, logging.ERROR, "provider_transport_error", provider="openai")
        raise ProviderInternalError("Failed to reach OpenAI.", provider="openai") from exc
    latency_ms = int((time.perf_counter() - t0) * 1000)
    if resp.status_code == 429:
        log_event(logger, logging.WARNING, "provider_rate_limit", provider="openai")
        raise ProviderRateLimitError("OpenAI rate limit exceeded.", provider="openai")
    if 400 <= resp.status_code < 500:
        log_event(logger, logging.WARNING, "provider_validation_error", provider="openai", status=resp.status_code)
        raise ProviderValidationError(
            f"OpenAI rejected the request (status {resp.status_code}).",
            provider="openai",
        )
    if resp.status_code >= 500:
        log_event(logger, logging.ERROR, "provider_internal_error", provider="openai", status=resp.status_code)
        raise ProviderInternalError("OpenAI upstream error.", provider="openai")
    try:
        data = resp.json()
    except ValueError as exc:
        log_event(logger, logging.ERROR, "provider_malformed_response", provider="openai")
        raise ProviderInternalError("OpenAI returned a malformed response.", provider="openai") from exc

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    output_text = message.get("content", "")

    usage = data.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens", 0))
    completion_tokens = int(usage.get("completion_tokens", 0))

    breakdown = compute_costs(
        provider="openai",
        model=model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    cost_usd = breakdown.total_cost

    provenance = {
        "provider": "openai",
        "model": model,
        "mode": "chat.completions",
        "input_tokens": int(prompt_tokens),
        "output_tokens": int(completion_tokens),
    }

    log_event(
        logger,
        logging.INFO,
        "provider_success",
        provider="openai",
        model=model,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
    )

    return {
        "output": output_text,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "confidence": 0.9,
        "provenance": provenance,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
