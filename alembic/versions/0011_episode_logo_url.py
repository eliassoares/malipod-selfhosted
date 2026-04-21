"""add episode logo url

Revision ID: 0011_episode_logo_url
Revises: 0010_podcast_feed_metadata
Create Date: 2026-04-21
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0011_episode_logo_url"
down_revision = "0010_podcast_feed_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "episodes",
        sa.Column(
            "logo_url",
            sa.String(512),
            nullable=False,
            server_default="/static/placeholders/lilith.png",
        ),
    )


def downgrade() -> None:
    op.drop_column("episodes", "logo_url")
