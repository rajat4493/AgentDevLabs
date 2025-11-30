from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr

from models.tenant import AutonomyLevel, DataSensitivity


class TenantBase(BaseModel):
    id: UUID
    name: str
    slug: str
    region: str
    governance_mode: str
    cost_mode: str
    status: str
    default_data_sensitivity: DataSensitivity
    default_autonomy_level: AutonomyLevel


class TenantRead(TenantBase):
    allowed_providers: List[str]
    max_band: str
    credit_limit_usd: Decimal
    usage_usd: Decimal
    max_daily_requests: int
    max_tokens_per_request: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    is_owner: bool
    tenant: TenantRead

    class Config:
        from_attributes = True


class TenantSettingsUpdate(BaseModel):
    default_data_sensitivity: DataSensitivity | None = None
    default_autonomy_level: AutonomyLevel | None = None
