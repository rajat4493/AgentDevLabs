"""Ensure tenant enums use uppercase values."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202502292102"
down_revision = "202502292101"
branch_labels = None
depends_on = None


RENAME_TPL = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = '{type_name}' AND e.enumlabel = '{old}'
    ) THEN
        ALTER TYPE {type_name} RENAME VALUE '{old}' TO '{new}';
    END IF;
END $$;
"""


def rename_enum_value(type_name: str, old: str, new: str) -> None:
    op.execute(RENAME_TPL.format(type_name=type_name, old=old, new=new))


def upgrade() -> None:
    rename_enum_value("tenantregion", "eu", "EU")
    rename_enum_value("tenantregion", "us", "US")
    rename_enum_value("tenantregion", "other", "OTHER")

    rename_enum_value("governancemode", "standard", "STANDARD")
    rename_enum_value("governancemode", "relaxed", "RELAXED")
    rename_enum_value("governancemode", "strict", "STRICT")

    rename_enum_value("costmode", "cost", "COST")
    rename_enum_value("costmode", "balanced", "BALANCED")
    rename_enum_value("costmode", "quality", "QUALITY")

    rename_enum_value("tenantband", "low", "LOW")
    rename_enum_value("tenantband", "medium", "MEDIUM")
    rename_enum_value("tenantband", "high", "HIGH")
    rename_enum_value("tenantband", "premium", "PREMIUM")

    rename_enum_value("tenantstatus", "active", "ACTIVE")
    rename_enum_value("tenantstatus", "suspended", "SUSPENDED")

    op.execute(
        sa.text(
            """
            UPDATE tenants
            SET region='EU',
                governance_mode='STANDARD',
                cost_mode='BALANCED',
                max_band='HIGH',
                status='ACTIVE'
            WHERE slug='default'
            """
        )
    )


def downgrade() -> None:
    rename_enum_value("tenantstatus", "ACTIVE", "active")
    rename_enum_value("tenantstatus", "SUSPENDED", "suspended")

    rename_enum_value("tenantband", "LOW", "low")
    rename_enum_value("tenantband", "MEDIUM", "medium")
    rename_enum_value("tenantband", "HIGH", "high")
    rename_enum_value("tenantband", "PREMIUM", "premium")

    rename_enum_value("costmode", "COST", "cost")
    rename_enum_value("costmode", "BALANCED", "balanced")
    rename_enum_value("costmode", "QUALITY", "quality")

    rename_enum_value("governancemode", "STANDARD", "standard")
    rename_enum_value("governancemode", "RELAXED", "relaxed")
    rename_enum_value("governancemode", "STRICT", "strict")

    rename_enum_value("tenantregion", "EU", "eu")
    rename_enum_value("tenantregion", "US", "us")
    rename_enum_value("tenantregion", "OTHER", "other")
