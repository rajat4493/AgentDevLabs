"""
Router endpoint that wraps provider selection + trace creation.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.traces import create_trace_record
from backend.db import get_session
from backend import schemas
from backend.pricing import estimate_cost
from backend.providers import PROVIDERS
from backend.router import new_run_id
from backend.router.complexity import choose_band, score_complexity
from backend.router.rule_based import select_model

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


@router.post("/chat", response_model=schemas.ChatResponse)
def route_chat(request: schemas.ChatRequest, db: Session = Depends(get_session)) -> schemas.ChatResponse:
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="prompt is required")

    complexity_score = score_complexity(prompt)
    inferred_band = choose_band(complexity_score, prompt)
    requested_band = request.band or inferred_band

    selection = select_model(
        band=requested_band,
        task_type=request.task_type,
        force_provider=request.provider,
        force_model=request.model,
    )
    provider_key = selection.provider.lower()
    adapter = PROVIDERS.get(provider_key)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{provider_key}' is not configured",
        )

    plan_params: Dict[str, Any] = dict(request.params or {})
    plan_params.setdefault("prompt", prompt)
    plan = adapter.plan(plan_params, selection.model)
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
        cost_usd = _safe_float(result.get("cost_usd"))
        if cost_usd is None and total_tokens is not None:
            cost_usd = estimate_cost(selection.model, prompt_tokens, completion_tokens)
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
        cost_usd = None

    run_id = new_run_id()
    trace_payload = schemas.TraceCreate(
        provider=provider_key,
        model=selection.model,
        input=prompt,
        output=output_text,
        tokens=total_tokens,
        latency_ms=latency_value,
        framework=request.framework or "raw",
        source=request.source or "router",
        status=status_value,
        error_message=error_message,
        extra=_merge_metadata(
            request.metadata,
            {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": cost_usd,
                "band": selection.band,
                "requested_band": requested_band,
                "inferred_band": inferred_band,
                "task_type": request.task_type,
                "route_source": selection.route_source,
                "run_id": run_id,
                "plan": plan,
                "provenance": result.get("provenance"),
            },
        ),
    )
    trace = create_trace_record(db, trace_payload)

    if status_value == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM call failed",
        )

    return schemas.ChatResponse(
        output=output_text,
        provider=provider_key,
        model=selection.model,
        tokens=total_tokens,
        latency_ms=latency_value,
        prompt_tokens=prompt_tokens or None,
        completion_tokens=completion_tokens or None,
        cost_usd=cost_usd,
        trace_id=trace.id,
        band=selection.band,
        route_source=selection.route_source,
    )


__all__ = ["router"]
