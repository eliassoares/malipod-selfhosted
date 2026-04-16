"""create subscription sync history

Revision ID: 0004_subscription_sync_history
Revises: 0003_device_sync_entities
Create Date: 2026-04-16
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_subscription_sync_history"
down_revision = "0003_device_sync_entities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscription_change_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_pk", sa.Integer(), nullable=False),
        sa.Column("feed_url", sa.String(length=512), nullable=False),
        sa.Column("operation", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_pk"],
            ["devices.id"],
            name=op.f("fk_subscription_change_events_device_pk_devices"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscription_change_events")),
    )


def downgrade() -> None:
    op.drop_table("subscription_change_events")
