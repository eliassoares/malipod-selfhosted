"""add episode playlists

Revision ID: 0016_episode_playlists
Revises: 0015_centralize_sync
Create Date: 2026-04-25
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0016_episode_playlists"
down_revision = "0015_centralize_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "episode_playlists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
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
            name=op.f("fk_episode_playlists_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_episode_playlists")),
        sa.UniqueConstraint(
            "user_id",
            "title",
            name="uq_episode_playlists_user_id_title",
        ),
    )
    op.create_index(
        "ix_episode_playlists_user_id",
        "episode_playlists",
        ["user_id"],
    )

    op.create_table(
        "episode_playlist_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("playlist_id", sa.Integer(), nullable=False),
        sa.Column("episode_id", sa.Integer(), nullable=False),
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
            name=op.f("fk_episode_playlist_items_episode_id_episodes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["playlist_id"],
            ["episode_playlists.id"],
            name=op.f("fk_episode_playlist_items_playlist_id_episode_playlists"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_episode_playlist_items")),
        sa.UniqueConstraint(
            "playlist_id",
            "episode_id",
            name="uq_episode_playlist_items_playlist_id_episode_id",
        ),
    )
    op.create_index(
        "ix_episode_playlist_items_playlist_id",
        "episode_playlist_items",
        ["playlist_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_episode_playlist_items_playlist_id",
        table_name="episode_playlist_items",
    )
    op.drop_table("episode_playlist_items")
    op.drop_index("ix_episode_playlists_user_id", table_name="episode_playlists")
    op.drop_table("episode_playlists")
