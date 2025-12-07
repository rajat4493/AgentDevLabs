"""
Aggregated stats endpoints.
"""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import models
from backend.db import get_session

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_session)) -> dict[str, object]:
    total_traces = db.query(func.count(models.Trace.id)).scalar() or 0

    avg_latency = db.query(func.avg(models.Trace.latency_ms)).scalar()
    avg_tokens = db.query(func.avg(models.Trace.tokens)).scalar()

    provider_counts_query = (
        db.query(models.Trace.provider, func.count(models.Trace.id))
        .group_by(models.Trace.provider)
        .all()
    )
    provider_counts = {provider or "unknown": count for provider, count in provider_counts_query}

    model_counts_query = (
        db.query(models.Trace.model, func.count(models.Trace.id))
        .group_by(models.Trace.model)
        .all()
    )
    model_counts = {model or "unknown": count for model, count in model_counts_query}

    daily_counts_query = (
        db.query(func.date(models.Trace.created_at), func.count(models.Trace.id))
        .group_by(func.date(models.Trace.created_at))
        .order_by(func.date(models.Trace.created_at))
        .all()
    )
    daily_counts = [
        {"date": date.isoformat() if hasattr(date, "isoformat") else str(date), "count": count}
        for date, count in daily_counts_query
    ]

    return {
        "total_traces": int(total_traces),
        "avg_latency_ms": float(avg_latency) if avg_latency is not None else None,
        "avg_tokens": float(avg_tokens) if avg_tokens is not None else None,
        "provider_counts": provider_counts,
        "model_counts": model_counts,
        "daily_counts": daily_counts,
    }


__all__ = ["router"]
