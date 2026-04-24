"""add centralized sync toggle

Revision ID: 0015_centralize_sync
Revises: 0014_episode_media_url
Create Date: 2026-04-24
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0015_centralize_sync"
down_revision = "0014_episode_media_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "centralize_sync",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "centralize_sync")
