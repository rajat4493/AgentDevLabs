"""
Core service logic for Lattice /v1 endpoints.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .cache import CacheDisabled, get_cache, make_cache_key
from .cost import compute_costs
from .errors import ConfigurationError, ProviderValidationError
from .logging import configure_logger, log_event
from .metrics import METRICS
from .pii import detect_tags
from .providers import PROVIDERS
from .router.bands import find_provider_for_model, select_model_for_band
from .router.complexity import choose_band, score_complexity

logger = configure_logger("lattice.service")


class CompleteRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    band: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _normalize_band(band: Optional[str]) -> Optional[str]:
    if not band:
        return None
    mapping = {
        "simple": "low",
        "low": "low",
        "moderate": "mid",
        "mid": "mid",
        "medium": "mid",
        "complex": "high",
        "high": "high",
        "long_context": "high",
    }
    return mapping.get(band.lower(), band)


def _choose_target(request: CompleteRequest, prompt: str) -> Dict[str, Any]:
    inferred_band = choose_band(score_complexity(prompt), prompt)
    requested_band = _normalize_band(request.band) or inferred_band

    if request.model:
        provider = (request.provider or find_provider_for_model(request.model) or "").lower()
        if not provider:
            raise ProviderValidationError(
                "provider must be specified when forcing a model",
                provider=request.provider,
            )
        return {
            "provider": provider,
            "model": request.model,
            "band": requested_band,
            "routing_reason": "forced_model",
        }

    try:
        provider, model, routing_reason = select_model_for_band(
            band=requested_band, explicit_provider=request.provider
        )
    except ValueError as exc:
        raise ConfigurationError(str(exc))
    return {
        "provider": provider,
        "model": model,
        "band": requested_band,
        "routing_reason": routing_reason,
    }


def complete(request: CompleteRequest) -> Dict[str, Any]:
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise ProviderValidationError("prompt is required")

    selection = _choose_target(request, prompt)
    provider_key: str = selection["provider"]
    model_name: str = selection["model"]
    resolved_band = selection["band"]
    routing_reason = selection["routing_reason"]

    adapter = PROVIDERS.get(provider_key)
    if not adapter:
        raise ProviderValidationError(f"provider '{provider_key}' unavailable", provider=provider_key)

    cache_key: Optional[str] = None
    cache_client = None
    cached_response: Optional[Dict[str, Any]] = None
    try:
        cache_client = get_cache()
        cache_key = make_cache_key(
            prompt=prompt,
            provider=provider_key,
            model=model_name,
            band=resolved_band,
            extra=request.metadata or {},
        )
        cached_response = cache_client.get(cache_key)
    except CacheDisabled:
        cache_client = None
    except Exception:
        cache_client = None

    prompt_tags = detect_tags(prompt)

    if cached_response:
        response_tags = detect_tags(cached_response.get("text", ""))
        tags = sorted(set(prompt_tags + response_tags))
        result = dict(cached_response)
        result["tags"] = tags
        latency_snapshot = int(result.get("latency_ms", 0) or 0)
        METRICS.increment_cache_hit()
        METRICS.increment_requests(
            provider=provider_key,
            model=model_name,
            band=resolved_band,
            latency_ms=latency_snapshot,
            input_tokens=0,
            output_tokens=0,
            total_cost=0.0,
            pii_tags_count=len(tags),
        )
        log_event(
            logger,
            logging.INFO,
            "completion_cache_hit",
            provider=provider_key,
            model=model_name,
            band=resolved_band,
            latency_ms=latency_snapshot,
            cache="hit",
            piitag=len(tags),
        )
        return result

    t0 = time.perf_counter()
    plan = adapter.plan(request.metadata or {}, model_name)
    raw_result = adapter.execute(plan, prompt)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    prompt_tokens = int(raw_result.get("prompt_tokens") or 0)
    completion_tokens = int(raw_result.get("completion_tokens") or 0)

    cost = compute_costs(
        provider=provider_key,
        model=model_name,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )

    response_text = raw_result.get("output", "")
    response_tags = detect_tags(response_text)
    tags = sorted(set(prompt_tags + response_tags))

    response_payload = {
        "text": response_text,
        "provider": provider_key,
        "model": model_name,
        "usage": {
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
        },
        "cost": cost.to_dict(),
        "latency_ms": latency_ms,
        "band": resolved_band,
        "routing_reason": routing_reason,
        "tags": tags,
    }

    if cache_key and cache_client:
        try:
            cache_client.set(cache_key, response_payload)
        except Exception:
            pass

    METRICS.increment_cache_miss()
    METRICS.increment_requests(
        provider=provider_key,
        model=model_name,
        band=resolved_band,
        latency_ms=latency_ms,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        total_cost=cost.total_cost,
        pii_tags_count=len(tags),
    )
    log_event(
        logger,
        logging.INFO,
        "completion_success",
        provider=provider_key,
        model=model_name,
        band=resolved_band,
        latency_ms=latency_ms,
        total_cost=cost.total_cost,
        cache="miss",
        piitag=len(tags),
    )

    return response_payload
