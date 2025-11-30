from __future__ import annotations

import enum
import uuid
from typing import List, Sequence

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.models import Base


class TenantRegion(enum.Enum):
    EU = "EU"
    US = "US"
    OTHER = "OTHER"


class GovernanceMode(enum.Enum):
    STANDARD = "STANDARD"
    RELAXED = "RELAXED"
    STRICT = "STRICT"


class CostMode(enum.Enum):
    COST = "COST"
    BALANCED = "BALANCED"
    QUALITY = "QUALITY"


class TenantStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class TenantBand(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    PREMIUM = "PREMIUM"


class DataSensitivity(enum.Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PII = "PII"


class AutonomyLevel(enum.Enum):
    ANSWER_ONLY = "ANSWER_ONLY"
    TOOL_CALL = "TOOL_CALL"


def _default_allowed_providers() -> List[str]:
    return ["openai", "gemini", "anthropic", "ollama"]


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    region: Mapped[TenantRegion] = mapped_column(
        SAEnum(TenantRegion), nullable=False, default=TenantRegion.EU
    )
    governance_mode: Mapped[GovernanceMode] = mapped_column(
        SAEnum(GovernanceMode), nullable=False, default=GovernanceMode.STANDARD
    )
    cost_mode: Mapped[CostMode] = mapped_column(
        SAEnum(CostMode), nullable=False, default=CostMode.BALANCED
    )
    allowed_providers: Mapped[Sequence[str]] = mapped_column(
        JSONB, nullable=False, default=_default_allowed_providers
    )
    max_band: Mapped[TenantBand] = mapped_column(
        SAEnum(TenantBand), nullable=False, default=TenantBand.HIGH
    )
    default_data_sensitivity: Mapped[DataSensitivity] = mapped_column(
        SAEnum(DataSensitivity, name="datasensitivity"),
        nullable=False,
        default=DataSensitivity.PUBLIC,
        server_default=DataSensitivity.PUBLIC.value,
    )
    default_autonomy_level: Mapped[AutonomyLevel] = mapped_column(
        SAEnum(AutonomyLevel, name="autonomylevel"),
        nullable=False,
        default=AutonomyLevel.ANSWER_ONLY,
        server_default=AutonomyLevel.ANSWER_ONLY.value,
    )
    credit_limit_usd: Mapped[Numeric] = mapped_column(
        Numeric(10, 2), nullable=False, default=5.00
    )
    usage_usd: Mapped[Numeric] = mapped_column(
        Numeric(12, 4), nullable=False, default=0
    )
    max_daily_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    max_tokens_per_request: Mapped[int] = mapped_column(
        Integer, nullable=False, default=4000
    )
    status: Mapped[TenantStatus] = mapped_column(
        SAEnum(TenantStatus), nullable=False, default=TenantStatus.ACTIVE
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    users: Mapped[List["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    is_owner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="users")
