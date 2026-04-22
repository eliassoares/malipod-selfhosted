"""add favorite podcasts table

Revision ID: 0013_favorite_podcasts
Revises: 0012_text_description_columns
Create Date: 2026-04-22
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0013_favorite_podcasts"
down_revision = "0012_text_description_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "favorite_podcasts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "feed_id",
            sa.Integer(),
            sa.ForeignKey("podcast_feeds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("favorited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id",
            "feed_id",
            name="uq_favorite_podcasts_user_id_feed_id",
        ),
    )
    op.create_index(
        "ix_favorite_podcasts_user_id",
        "favorite_podcasts",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_favorite_podcasts_user_id", table_name="favorite_podcasts")
    op.drop_table("favorite_podcasts")
