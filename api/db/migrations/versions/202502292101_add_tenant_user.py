"""Add tenant and user tables."""

from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "202502292101"
down_revision = None
branch_labels = None
depends_on = None

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000010"


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column(
            "region",
            sa.Enum("EU", "US", "OTHER", name="tenantregion"),
            nullable=False,
            server_default="EU",
        ),
        sa.Column(
            "governance_mode",
            sa.Enum("STANDARD", "RELAXED", "STRICT", name="governancemode"),
            nullable=False,
            server_default="STANDARD",
        ),
        sa.Column(
            "cost_mode",
            sa.Enum("COST", "BALANCED", "QUALITY", name="costmode"),
            nullable=False,
            server_default="BALANCED",
        ),
        sa.Column(
            "allowed_providers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[\"openai\",\"gemini\",\"anthropic\",\"ollama\"]'::jsonb"),
        ),
        sa.Column(
            "max_band",
            sa.Enum("LOW", "MEDIUM", "HIGH", "PREMIUM", name="tenantband"),
            nullable=False,
            server_default="HIGH",
        ),
        sa.Column("credit_limit_usd", sa.Numeric(10, 2), nullable=False, server_default="5.00"),
        sa.Column("usage_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("max_daily_requests", sa.Integer, nullable=False, server_default="1000"),
        sa.Column("max_tokens_per_request", sa.Integer, nullable=False, server_default="4000"),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "SUSPENDED", name="tenantstatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_owner", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.add_column(
        "router_runs",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_router_runs_tenant_id", "router_runs", ["tenant_id"])

    op.execute(
        sa.text(
            """
            INSERT INTO tenants (
                id, name, slug, region, governance_mode, cost_mode, allowed_providers,
                max_band, credit_limit_usd, usage_usd, max_daily_requests,
                max_tokens_per_request, status
            ) VALUES (
                :id, 'Default Tenant', 'default', 'EU', 'STANDARD', 'BALANCED',
                :allowed, 'HIGH', 5.00, 0, 1000, 4000, 'ACTIVE'
            )
            """
        )
        .bindparams(
            id=DEFAULT_TENANT_ID,
            allowed=json.dumps(["openai", "gemini", "anthropic", "ollama"]),
        )
        .execution_options(autocommit=True)
    )
    op.execute(
        sa.text(
            """
            INSERT INTO users (id, email, password_hash, tenant_id, is_owner)
            VALUES (:id, 'demo@agenticlabs.local', 'hashed-changeme', :tenant_id, true)
            """
        )
        .bindparams(id=DEFAULT_USER_ID, tenant_id=DEFAULT_TENANT_ID)
        .execution_options(autocommit=True)
    )


def downgrade() -> None:
    op.drop_index("ix_router_runs_tenant_id", table_name="router_runs")
    op.drop_column("router_runs", "tenant_id")
    op.drop_table("users")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS tenantregion")
    op.execute("DROP TYPE IF EXISTS governancemode")
    op.execute("DROP TYPE IF EXISTS costmode")
    op.execute("DROP TYPE IF EXISTS tenantband")
    op.execute("DROP TYPE IF EXISTS tenantstatus")
