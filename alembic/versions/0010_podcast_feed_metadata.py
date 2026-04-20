"""add podcast feed metadata fields

Revision ID: 0010_podcast_feed_metadata
Revises: 0009_device_sync_groups
Create Date: 2026-04-20
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0010_podcast_feed_metadata"
down_revision = "0009_device_sync_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("podcast_feeds", sa.Column("author", sa.String(255), nullable=True))
    op.add_column("podcast_feeds", sa.Column("categories", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("podcast_feeds", "categories")
    op.drop_column("podcast_feeds", "author")
