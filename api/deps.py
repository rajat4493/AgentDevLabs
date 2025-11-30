import os
import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from config.router import get_router_mode, RouterMode
from db.session import get_db
from models.tenant import Tenant, TenantStatus


DEFAULT_TENANT_ID = os.getenv(
    "AGENTICLABS_DEFAULT_TENANT_ID",
    "00000000-0000-0000-0000-000000000001",
)


def get_router_mode_dep() -> RouterMode:
    return get_router_mode()


def _load_tenant(db: Session, identifier: str) -> Tenant | None:
    ident = identifier.strip().lower()
    tenant = None
    try:
        tenant_uuid = uuid.UUID(ident)
    except ValueError:
        tenant_uuid = None

    if tenant_uuid:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
    if not tenant:
        tenant = db.query(Tenant).filter(Tenant.slug == ident).first()
    return tenant


def get_tenant_dep(
    db: Session = Depends(get_db),
    tenant_header: str | None = Header(None, alias="X-Agentic-Tenant-Id"),
) -> Tenant:
    tenant_identifier = tenant_header or DEFAULT_TENANT_ID
    if not tenant_identifier:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant header missing",
        )

    tenant = _load_tenant(db, tenant_identifier)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is suspended",
        )
    return tenant
