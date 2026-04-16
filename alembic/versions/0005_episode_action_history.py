"""create episode action history

Revision ID: 0005_episode_action_history
Revises: 0004_subscription_sync_history
Create Date: 2026-04-16
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0005_episode_action_history"
down_revision = "0004_subscription_sync_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "episode_action_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("podcast_url", sa.String(length=512), nullable=False),
        sa.Column("episode_url", sa.String(length=512), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["episode_id"],
            ["episodes.id"],
            name=op.f("fk_episode_action_events_episode_id_episodes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_episode_action_events_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_episode_action_events")),
    )


def downgrade() -> None:
    op.drop_table("episode_action_events")
