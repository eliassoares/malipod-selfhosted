"""add media url to episodes

Revision ID: 0014_episode_media_url
Revises: 0013_favorite_podcasts
Create Date: 2026-04-22
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0014_episode_media_url"
down_revision = "0013_favorite_podcasts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("episodes", sa.Column("media_url", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("episodes", "media_url")
