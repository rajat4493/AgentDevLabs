"""
Trace management endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.db import get_session
from pydantic import BaseModel

router = APIRouter(prefix="/api/traces", tags=["traces"])

SchemaT = TypeVar("SchemaT", bound=schemas.ORMModel)


def _model_dump(payload: BaseModel) -> Dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return payload.dict()


def _to_schema(schema_cls: Type[SchemaT], instance: Any) -> SchemaT:
    if hasattr(schema_cls, "model_validate"):
        return schema_cls.model_validate(instance)  # type: ignore[attr-defined]
    return schema_cls.from_orm(instance)  # type: ignore[attr-defined]


def create_trace_record(db: Session, payload: schemas.TraceCreate) -> models.Trace:
    data = _model_dump(payload)
    trace = models.Trace(**data)
    db.add(trace)
    db.commit()
    db.refresh(trace)
    return trace


@router.post("", response_model=schemas.TraceRead, status_code=status.HTTP_201_CREATED)
def create_trace(payload: schemas.TraceCreate, db: Session = Depends(get_session)) -> schemas.TraceRead:
    trace = create_trace_record(db, payload)
    return _to_schema(schemas.TraceRead, trace)


@router.get("", response_model=schemas.TraceListResponse)
def list_traces(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    provider: str | None = Query(None),
    model: str | None = Query(None),
    framework: str | None = Query(None),
    source: str | None = Query(None),
    db: Session = Depends(get_session),
) -> schemas.TraceListResponse:
    filters = []
    if provider:
        filters.append(models.Trace.provider == provider)
    if model:
        filters.append(models.Trace.model == model)
    if framework:
        filters.append(models.Trace.framework == framework)
    if source:
        filters.append(models.Trace.source == source)

    base_stmt = select(models.Trace).where(*filters)
    page_stmt = (
        base_stmt.order_by(models.Trace.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = db.scalars(page_stmt).all()

    count_stmt = select(func.count()).select_from(
        select(models.Trace.id).where(*filters).subquery()
    )
    total = db.execute(count_stmt).scalar_one()

    serialized: List[schemas.TraceListItem] = [
        _to_schema(schemas.TraceListItem, item) for item in items
    ]
    return schemas.TraceListResponse(items=serialized, total=total, limit=limit, offset=offset)


@router.get("/{trace_id}", response_model=schemas.TraceRead)
def read_trace(trace_id: str, db: Session = Depends(get_session)) -> schemas.TraceRead:
    trace = db.get(models.Trace, trace_id)
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    return _to_schema(schemas.TraceRead, trace)


__all__ = ["router", "create_trace_record"]
