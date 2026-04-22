"""use TEXT for description columns in podcast_feeds and episodes

Revision ID: 0012_text_description_columns
Revises: 0011_episode_logo_url
Create Date: 2026-04-22
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0012_text_description_columns"
down_revision = "0011_episode_logo_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "podcast_feeds",
        "description",
        type_=sa.Text(),
        existing_type=sa.String(1000),
        existing_nullable=True,
    )
    op.alter_column(
        "episodes",
        "description",
        type_=sa.Text(),
        existing_type=sa.String(2000),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "episodes",
        "description",
        type_=sa.String(2000),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "podcast_feeds",
        "description",
        type_=sa.String(1000),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
