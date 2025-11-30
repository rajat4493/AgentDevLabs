"""Add governance defaults to tenant."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202502292103"
down_revision = "202502292102"
branch_labels = None
depends_on = None


data_sensitivity_enum = sa.Enum(
    "PUBLIC", "INTERNAL", "PII", name="datasensitivity"
)
autonomy_level_enum = sa.Enum(
    "ANSWER_ONLY", "TOOL_CALL", name="autonomylevel"
)


def upgrade() -> None:
    bind = op.get_bind()
    data_sensitivity_enum.create(bind, checkfirst=True)
    autonomy_level_enum.create(bind, checkfirst=True)

    op.add_column(
        "tenants",
        sa.Column(
            "default_data_sensitivity",
            data_sensitivity_enum,
            nullable=False,
            server_default="PUBLIC",
        ),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "default_autonomy_level",
            autonomy_level_enum,
            nullable=False,
            server_default="ANSWER_ONLY",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "default_autonomy_level")
    op.drop_column("tenants", "default_data_sensitivity")
    bind = op.get_bind()
    autonomy_level_enum.drop(bind, checkfirst=True)
    data_sensitivity_enum.drop(bind, checkfirst=True)
