"""add web player last state

Revision ID: 0017_web_player_last_state
Revises: 0016_episode_playlists
Create Date: 2026-04-25
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0017_web_player_last_state"
down_revision = "0016_episode_playlists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "last_episode_id",
            sa.Integer(),
            sa.ForeignKey("episodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column("last_position_sec", sa.Integer(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_queue_mode", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_queue_ref_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_queue_ref_id")
    op.drop_column("users", "last_queue_mode")
    op.drop_column("users", "last_position_sec")
    op.drop_column("users", "last_episode_id")
