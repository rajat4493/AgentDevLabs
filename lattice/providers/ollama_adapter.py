import logging
import time
from typing import Any, Dict

import requests

from ..config import settings
from ..errors import (
    ProviderInternalError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from ..logging import configure_logger, log_event

OLLAMA_BASE = settings.ollama_url.rstrip("/")
DEFAULT_MODEL = settings.ollama_model
TIMEOUT = 120  # seconds
logger = configure_logger("lattice.providers.ollama")


def _estimate_tokens(text: str) -> int:
    # crude heuristic ~4 chars per token
    return max(1, int(len(text) / 4))


def plan(req: Dict[str, Any], model_name: str | None = None) -> Dict[str, Any]:
    prompt = req.get("prompt", "")
    tokens = _estimate_tokens(prompt)
    model = model_name or DEFAULT_MODEL
    return {
        "target": {"provider": "ollama", "model": model},
        "est_tokens": tokens,
        "est_cost_usd": 0.0,
    }


def execute(plan: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    target = plan.get("target") or {}
    model = target.get("model") or DEFAULT_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    start = time.time()
    try:
        resp = requests.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=TIMEOUT)
    except requests.Timeout as exc:
        log_event(logger, logging.WARNING, "provider_timeout", provider="ollama")
        raise ProviderTimeoutError("Ollama did not respond in time.", provider="ollama") from exc
    except requests.RequestException as exc:
        log_event(logger, logging.ERROR, "provider_transport_error", provider="ollama")
        raise ProviderInternalError("Failed to reach Ollama.", provider="ollama") from exc

    if resp.status_code == 429:
        log_event(logger, logging.WARNING, "provider_rate_limit", provider="ollama")
        raise ProviderRateLimitError("Ollama rate limit exceeded.", provider="ollama")
    if 400 <= resp.status_code < 500:
        log_event(logger, logging.WARNING, "provider_validation_error", provider="ollama", status=resp.status_code)
        raise ProviderValidationError("Ollama rejected the request.", provider="ollama")
    if resp.status_code >= 500:
        log_event(logger, logging.ERROR, "provider_internal_error", provider="ollama", status=resp.status_code)
        raise ProviderInternalError("Ollama returned a server error.", provider="ollama")

    try:
        data = resp.json()
    except ValueError as exc:
        log_event(logger, logging.ERROR, "provider_malformed_response", provider="ollama")
        raise ProviderInternalError("Ollama returned malformed JSON.", provider="ollama") from exc

    output = data.get("response", "")

    latency_ms = int((time.time() - start) * 1000)
    tokens_in = _estimate_tokens(prompt)
    tokens_out = _estimate_tokens(output)

    log_event(
        logger,
        logging.INFO,
        "provider_success",
        provider="ollama",
        model=model,
        latency_ms=latency_ms,
        prompt_tokens=tokens_in,
        completion_tokens=tokens_out,
    )

    return {
        "output": output.strip(),
        "confidence": 0.9,
        "latency_ms": latency_ms,
        "cost_usd": 0.0,
        "prompt_tokens": tokens_in,
        "completion_tokens": tokens_out,
        "provenance": {
            "provider": "ollama",
            "model": model,
            "parameters": {"stream": False},
        },
    }
