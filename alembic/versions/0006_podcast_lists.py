"""create podcast list tables

Revision ID: 0006_podcast_lists
Revises: 0005_episode_action_history
Create Date: 2026-04-16
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0006_podcast_lists"
down_revision = "0005_episode_action_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "podcast_lists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
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
            ["user_id"],
            ["users.id"],
            name=op.f("fk_podcast_lists_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_podcast_lists")),
        sa.UniqueConstraint("user_id", "name", name="uq_podcast_lists_user_id_name"),
    )
    op.create_table(
        "podcast_list_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("list_id", sa.Integer(), nullable=False),
        sa.Column("feed_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
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
            ["feed_id"],
            ["podcast_feeds.id"],
            name=op.f("fk_podcast_list_items_feed_id_podcast_feeds"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["list_id"],
            ["podcast_lists.id"],
            name=op.f("fk_podcast_list_items_list_id_podcast_lists"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_podcast_list_items")),
        sa.UniqueConstraint(
            "list_id",
            "feed_id",
            name="uq_podcast_list_items_list_id_feed_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("podcast_list_items")
    op.drop_table("podcast_lists")
