"""add playlist item position

Revision ID: 0018_playlist_item_position
Revises: 0017_web_player_last_state
Create Date: 2026-04-25
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0018_playlist_item_position"
down_revision = "0017_web_player_last_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "episode_playlist_items",
        sa.Column("position", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_episode_playlist_items_playlist_id_position",
        "episode_playlist_items",
        ["playlist_id", "position"],
    )

    bind = op.get_bind()
    playlist_rows = bind.execute(sa.text("SELECT id FROM episode_playlists")).fetchall()
    for (playlist_id,) in playlist_rows:
        rows = bind.execute(
            sa.text(
                """
                SELECT id
                FROM episode_playlist_items
                WHERE playlist_id = :playlist_id
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"playlist_id": playlist_id},
        ).fetchall()
        for index, (item_id,) in enumerate(rows, start=1):
            bind.execute(
                sa.text(
                    "UPDATE episode_playlist_items SET position = :pos WHERE id = :id"
                ),
                {"pos": index, "id": item_id},
            )


def downgrade() -> None:
    op.drop_index(
        "ix_episode_playlist_items_playlist_id_position",
        table_name="episode_playlist_items",
    )
    op.drop_column("episode_playlist_items", "position")
