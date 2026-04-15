"""create foundation tables

Revision ID: 0001_foundation_tables
Revises:
Create Date: 2026-04-15
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_foundation_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "application_surfaces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("surface_name", sa.String(length=64), nullable=False),
        sa.Column("surface_type", sa.String(length=32), nullable=False),
        sa.Column("route_prefix", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_surfaces")),
        sa.UniqueConstraint(
            "surface_name",
            name=op.f("uq_application_surfaces_surface_name"),
        ),
    )
    op.create_table(
        "readiness_checks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("surface_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("detail", sa.String(length=255), nullable=False),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["surface_id"],
            ["application_surfaces.id"],
            name=op.f("fk_readiness_checks_surface_id_application_surfaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_readiness_checks")),
    )


def downgrade() -> None:
    op.drop_table("readiness_checks")
    op.drop_table("application_surfaces")
