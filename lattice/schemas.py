"""Pydantic schemas shared across the Lattice backend and SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    """User payload for ``POST /v1/complete``."""

    prompt: str = Field(..., min_length=1)
    band: Optional[Literal["low", "mid", "high"]] = Field(default=None)
    model: Optional[str] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Opaque user metadata, not logged.")


class UsageStats(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class CostInfo(BaseModel):
    currency: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    pricing_version: Optional[str] = None


class RoutingDecision(BaseModel):
    reason: str
    candidates: List[Dict[str, str]]
    chosen: Dict[str, str]


class CompletionResponse(BaseModel):
    text: str
    provider: str
    model: str
    band: Optional[str]
    latency_ms: float
    usage: UsageStats
    cost: CostInfo
    tags: List[str]
    routing: RoutingDecision


__all__ = [
    "CompletionRequest",
    "CompletionResponse",
    "UsageStats",
    "CostInfo",
    "RoutingDecision",
]
