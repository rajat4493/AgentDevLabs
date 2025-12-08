"""
Core service logic for Lattice /v1 endpoints.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from .cache import CacheDisabled, build_exact_cache_key, get_cache_client
from .cost import compute_costs
from .metrics import METRICS
from .pii import detect_tags
from .providers import PROVIDERS
from .router.bands import find_provider_for_model, select_model_for_band
from .router.complexity import choose_band, score_complexity


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


def _build_cache_payload(response: Dict[str, Any]) -> Dict[str, Any]:
    return {"response": response}


def _choose_target(request: CompleteRequest, prompt: str) -> Dict[str, Any]:
    inferred_band = choose_band(score_complexity(prompt), prompt)
    requested_band = _normalize_band(request.band) or inferred_band

    if request.model:
        provider = (request.provider or find_provider_for_model(request.model) or "").lower()
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="provider must be specified when forcing a model",
            )
        return {
            "provider": provider,
            "model": request.model,
            "band": requested_band,
            "routing_reason": "forced_model",
        }

    provider, model, routing_reason = select_model_for_band(
        band=requested_band, explicit_provider=request.provider
    )
    return {
        "provider": provider,
        "model": model,
        "band": requested_band,
        "routing_reason": routing_reason,
    }


def _cache_fingerprint(request: CompleteRequest, band: Optional[str], prompt: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "band": band,
        "provider": (request.provider or "").lower() if request.provider else None,
        "model": request.model,
    }
    return payload


def complete(request: CompleteRequest) -> Dict[str, Any]:
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="prompt is required")

    selection = _choose_target(request, prompt)
    provider_key: str = selection["provider"]
    model_name: str = selection["model"]
    resolved_band = selection["band"]
    routing_reason = selection["routing_reason"]

    adapter = PROVIDERS.get(provider_key)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"provider '{provider_key}' unavailable"
        )

    cache_key: Optional[str] = None
    cached_response: Optional[Dict[str, Any]] = None
    cache_hit = False
    try:
        fingerprint = _cache_fingerprint(request, resolved_band, prompt)
        cache_key = build_exact_cache_key(fingerprint)
        cached_entry = get_cache_client().get_json(cache_key)
        if cached_entry and isinstance(cached_entry.get("response"), dict):
            cached_response = cached_entry["response"]
            cache_hit = True
    except CacheDisabled:
        cache_key = None
    except Exception:
        cache_key = None

    prompt_tags = detect_tags(prompt)

    if cached_response:
        response_tags = detect_tags(cached_response.get("text", ""))
        tags = sorted(set(prompt_tags + response_tags))
        result = dict(cached_response)
        result["tags"] = tags
        METRICS.record_request(
            provider=provider_key,
            model=model_name,
            band=resolved_band,
            latency_ms=result.get("latency_ms", 0) or 0,
            input_tokens=result.get("usage", {}).get("input_tokens", 0),
            output_tokens=result.get("usage", {}).get("output_tokens", 0),
            total_cost=result.get("cost", {}).get("total_cost", 0.0),
            cache_hit=True,
            tags=tags,
            count_usage=False,
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

    if cache_key:
        try:
            client = get_cache_client()
            client.set_json(cache_key, _build_cache_payload(response_payload))
        except CacheDisabled:
            pass
        except Exception:
            pass

    METRICS.record_request(
        provider=provider_key,
        model=model_name,
        band=resolved_band,
        latency_ms=latency_ms,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        total_cost=cost.total_cost,
        cache_hit=False,
        tags=tags,
        count_usage=True,
    )

    return response_payload
