"""
Router endpoint that wraps provider selection + trace creation.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.traces import create_trace_record
from backend.db import get_session
from backend import schemas
from backend.cache import CacheDisabled, build_exact_cache_key, get_cache_client
from backend.cost import compute_costs
from backend.providers import PROVIDERS
from backend.router import new_run_id
from backend.router.bands import find_provider_for_model, select_model_for_band
from backend.router.complexity import choose_band, score_complexity

router = APIRouter(prefix="/api", tags=["router"])


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _merge_metadata(base: Dict[str, Any] | None, extra: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    if base:
        merged.update(base)
    merged.update(extra)
    return merged


def _resolve_forced_model(request: schemas.ChatRequest) -> tuple[str, str, str]:
    """
    When the caller forces a model, derive provider from request or band registry.
    """

    model = (request.model or "").strip()
    if not model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="model is required")
    provider = (request.provider or find_provider_for_model(model) or "unknown").lower()
    return provider, model, "forced_model"


_BAND_NORMALIZATION = {
    "simple": "low",
    "low": "low",
    "moderate": "mid",
    "medium": "mid",
    "complex": "high",
    "high": "high",
    "long_context": "high",
}


def _normalize_band(band: str | None) -> Optional[str]:
    if not band:
        return None
    return _BAND_NORMALIZATION.get(band.lower(), band)


def _build_cache_fingerprint(request: schemas.ChatRequest, normalized_band: Optional[str]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "prompt": (request.prompt or "").strip(),
        "band": normalized_band,
        "provider": (request.provider or "").lower() if request.provider else None,
        "model": request.model,
        "task_type": request.task_type,
    }
    params = request.params or {}
    if params:
        payload["params"] = {k: params[k] for k in sorted(params)}
    return payload


def _respond_from_cache(
    *,
    cached_response: Dict[str, Any],
    cached_base_extra: Dict[str, Any],
    request: schemas.ChatRequest,
    prompt: str,
    inferred_band: str,
    requested_band: Optional[str],
    db: Session,
) -> schemas.ChatResponse:
    provider_key = (cached_response.get("provider") or "").lower()
    model_name = cached_response.get("model")
    if not provider_key or not model_name:
        raise ValueError("Cached payload missing provider/model.")

    selected_band = cached_response.get("band") or requested_band or "mid"
    routing_reason_raw = cached_response.get("route_source") or "band:cache"
    routing_reason = f"cache_hit;{routing_reason_raw}".rstrip(";")
    prompt_tokens = _safe_int(cached_response.get("prompt_tokens"))
    completion_tokens = _safe_int(cached_response.get("completion_tokens"))
    total_tokens = cached_response.get("tokens")
    latency_value = _safe_int(cached_response.get("latency_ms"))
    cost_payload = cached_response.get("cost") or {}
    cost_usd = cached_response.get("cost_usd")

    extra_base = dict(cached_base_extra or {})
    extra_base.update(
        {
            "band": selected_band,
            "requested_band": requested_band,
            "inferred_band": inferred_band,
            "task_type": request.task_type,
            "route_source": routing_reason,
        }
    )
    run_id = new_run_id()
    extra_payload = _merge_metadata(request.metadata, {**extra_base, "run_id": run_id})

    trace_payload = schemas.TraceCreate(
        provider=provider_key,
        model=model_name,
        input=prompt,
        output=cached_response.get("output", ""),
        tokens=total_tokens,
        latency_ms=latency_value,
        framework=request.framework or "raw",
        source=request.source or "router",
        status="success",
        error_message=None,
        extra=extra_payload,
    )
    trace = create_trace_record(db, trace_payload)

    return schemas.ChatResponse(
        output=cached_response.get("output", ""),
        provider=provider_key,
        model=model_name,
        tokens=total_tokens,
        latency_ms=latency_value,
        prompt_tokens=prompt_tokens or None,
        completion_tokens=completion_tokens or None,
        cost_usd=cost_usd,
        cost=cost_payload,
        trace_id=trace.id,
        band=selected_band,
        route_source=routing_reason,
    )


@router.post("/chat", response_model=schemas.ChatResponse)
def route_chat(request: schemas.ChatRequest, db: Session = Depends(get_session)) -> schemas.ChatResponse:
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="prompt is required")

    complexity_score = score_complexity(prompt)
    inferred_band = choose_band(complexity_score, prompt)
    requested_band = request.band or inferred_band
    normalized_band = _normalize_band(requested_band)
    selected_band_value = normalized_band or requested_band or "mid"

    cache_key: Optional[str] = None
    cached_entry: Optional[Dict[str, Any]] = None
    try:
        fingerprint = _build_cache_fingerprint(request, normalized_band)
        cache_key = build_exact_cache_key(fingerprint)
        cached_entry = get_cache_client().get_json(cache_key)
    except CacheDisabled:
        cache_key = None
    except Exception:
        cache_key = None
        cached_entry = None

    if cached_entry:
        cached_response = cached_entry.get("response")
        cached_base_extra = cached_entry.get("base_extra") or {}
        if isinstance(cached_response, dict):
            try:
                return _respond_from_cache(
                    cached_response=cached_response,
                    cached_base_extra=cached_base_extra,
                    request=request,
                    prompt=prompt,
                    inferred_band=inferred_band,
                    requested_band=requested_band,
                    db=db,
                )
            except Exception:
                cached_entry = None

    if request.model:
        provider_key, selected_model, routing_reason = _resolve_forced_model(request)
    else:
        try:
            provider_name, selected_model, routing_reason = select_model_for_band(
                band=normalized_band,
                explicit_provider=request.provider,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        provider_key = provider_name.lower()
        if routing_reason.startswith("band:"):
            selected_band_value = routing_reason.split(":", 1)[1]
    adapter = PROVIDERS.get(provider_key)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider_key}' is not configured",
        )

    plan_params: Dict[str, Any] = dict(request.params or {})
    plan_params.setdefault("prompt", prompt)
    plan = adapter.plan(plan_params, selected_model)
    t0 = time.perf_counter()

    status_value = "success"
    error_message = None
    measured_latency = None
    try:
        result = adapter.execute(plan, prompt)
        measured_latency = int((time.perf_counter() - t0) * 1000)
        output_text = (result.get("output") or "").strip()
        prompt_tokens = _safe_int(result.get("prompt_tokens"))
        completion_tokens = _safe_int(result.get("completion_tokens"))
        total_tokens = (prompt_tokens + completion_tokens) or None
        latency_ms = result.get("latency_ms")
        latency_value = _safe_int(latency_ms) if latency_ms is not None else measured_latency
        adapter_cost = _safe_float(result.get("cost_usd"))
    except Exception as exc:  # noqa: BLE001
        status_value = "error"
        error_message = repr(exc)
        measured_latency = int((time.perf_counter() - t0) * 1000)
        result = {}
        output_text = ""
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = None
        latency_value = measured_latency
        adapter_cost = None

    cost_breakdown = compute_costs(
        provider=provider_key,
        model=selected_model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
    )
    cost_usd = adapter_cost if adapter_cost is not None else cost_breakdown.total_cost
    cost_payload = cost_breakdown.to_dict()
    selected_band = selected_band_value or requested_band or "mid"

    response_payload: Dict[str, Any] = {
        "output": output_text,
        "provider": provider_key,
        "model": selected_model,
        "tokens": total_tokens,
        "latency_ms": latency_value,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd,
        "cost": cost_payload,
        "band": selected_band,
        "route_source": routing_reason,
    }
    base_extra: Dict[str, Any] = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd,
        "cost": cost_payload,
        "band": selected_band,
        "requested_band": requested_band,
        "inferred_band": inferred_band,
        "task_type": request.task_type,
        "route_source": routing_reason,
        "plan": plan,
        "provenance": result.get("provenance"),
    }

    run_id = new_run_id()
    trace_payload = schemas.TraceCreate(
        provider=provider_key,
        model=selected_model,
        input=prompt,
        output=output_text,
        tokens=total_tokens,
        latency_ms=latency_value,
        framework=request.framework or "raw",
        source=request.source or "router",
        status=status_value,
        error_message=error_message,
        extra=_merge_metadata(request.metadata, {**base_extra, "run_id": run_id}),
    )
    trace = create_trace_record(db, trace_payload)

    if status_value == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM call failed",
        )

    if cache_key and status_value == "success":
        cache_entry = {"response": response_payload, "base_extra": base_extra}
        try:
            cache = get_cache_client()
            cache.set_json(cache_key, cache_entry, ttl_seconds=300)
        except CacheDisabled:
            pass
        except Exception:
            pass

    return schemas.ChatResponse(
        output=response_payload["output"],
        provider=response_payload["provider"],
        model=response_payload["model"],
        tokens=response_payload["tokens"],
        latency_ms=response_payload["latency_ms"],
        prompt_tokens=response_payload["prompt_tokens"] or None,
        completion_tokens=response_payload["completion_tokens"] or None,
        cost_usd=response_payload["cost_usd"],
        cost=response_payload["cost"],
        trace_id=trace.id,
        band=response_payload["band"],
        route_source=response_payload["route_source"],
    )


__all__ = ["router"]
