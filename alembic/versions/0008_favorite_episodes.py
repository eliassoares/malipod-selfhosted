"""create favorite episodes table

Revision ID: 0008_favorite_episodes
Revises: 0007_settings_api
Create Date: 2026-04-17
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0008_favorite_episodes"
down_revision = "0007_settings_api"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "favorite_episodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("favorited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["episode_id"],
            ["episodes.id"],
            name=op.f("fk_favorite_episodes_episode_id_episodes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_favorite_episodes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorite_episodes")),
        sa.UniqueConstraint(
            "user_id",
            "episode_id",
            name="uq_favorite_episodes_user_id_episode_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("favorite_episodes")
