"""
Pydantic schemas shared by the RAJOS backend and SDK.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

try:  # pragma: no cover - compatibility with pydantic v1/v2
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover
    ConfigDict = None  # type: ignore


class ORMModel(BaseModel):
    """
    Base class that enables `from_orm`/`model_validate` usage across Pydantic versions.
    """

    if ConfigDict is not None:  # pragma: no cover - executed at import
        model_config = ConfigDict(from_attributes=True)
    else:  # pragma: no cover
        class Config:
            orm_mode = True


class TraceBase(BaseModel):
    provider: str = Field(..., description="LLM provider identifier, e.g., openai")
    model: str = Field(..., description="Specific model used for the call")
    input: str = Field(..., description="Prompt/input text")
    output: Optional[str] = Field(None, description="LLM output text")
    tokens: Optional[int] = Field(None, description="Total tokens (prompt + completion)")
    latency_ms: Optional[int] = Field(None, description="Measured latency in milliseconds")
    framework: Optional[str] = Field(None, description="SDK/framework that generated the trace")
    source: Optional[str] = Field(None, description="Where the trace came from (router/sdk/playground)")
    extra: Optional[Dict[str, Any]] = Field(None, description="Arbitrary metadata blob")


class TraceCreate(TraceBase):
    pass


class TraceRead(ORMModel):
    id: str
    created_at: datetime
    provider: str
    model: str
    input: str
    output: Optional[str] = None
    tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    framework: Optional[str] = None
    source: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class TraceListItem(ORMModel):
    id: str
    created_at: datetime
    provider: str
    model: str
    latency_ms: Optional[int] = None
    framework: Optional[str] = None
    source: Optional[str] = None


class TraceListResponse(BaseModel):
    items: List[TraceListItem]
    total: int
    limit: int
    offset: int


class ChatRequest(BaseModel):
    prompt: str
    task_type: Optional[str] = Field(None, description="Optional hint for routing rules")
    band: Optional[str] = Field(None, description="Force-routing band override")
    provider: Optional[str] = Field(None, description="Force a specific provider")
    model: Optional[str] = Field(None, description="Force a specific model")
    framework: Optional[str] = Field(None, description="Name of the calling framework/sdk")
    source: Optional[str] = Field("router", description="High-level source for attribution")
    metadata: Optional[Dict[str, Any]] = Field(None, description="User supplied metadata")
    params: Optional[Dict[str, Any]] = Field(
        None, description="Adapter specific overrides such as temperature/max_tokens"
    )


class ChatResponse(BaseModel):
    output: str
    provider: str
    model: str
    tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    trace_id: str
    band: str
    route_source: str


__all__ = [
    "TraceBase",
    "TraceCreate",
    "TraceRead",
    "TraceListItem",
    "TraceListResponse",
    "ChatRequest",
    "ChatResponse",
]
