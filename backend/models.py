"""
SQLAlchemy models for the RAJOS backend.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, func

from .db import Base


class Trace(Base):
    __tablename__ = "traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    provider = Column(String(32), nullable=False, index=True)
    model = Column(String(128), nullable=False, index=True)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    framework = Column(String(64), nullable=True)
    source = Column(String(64), nullable=True)
    extra = Column(JSON, nullable=True, default=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "provider": self.provider,
            "model": self.model,
            "input": self.input,
            "output": self.output,
            "tokens": self.tokens,
            "latency_ms": self.latency_ms,
            "framework": self.framework,
            "source": self.source,
            "extra": self.extra,
        }


__all__ = ["Trace"]
