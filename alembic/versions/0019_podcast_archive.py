"""podcast archive flags and episode archive state

Revision ID: 0019_podcast_archive
Revises: 0018_playlist_item_position
Create Date: 2026-04-27
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0019_podcast_archive"
down_revision = "0018_playlist_item_position"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "podcast_feeds",
        sa.Column(
            "archive",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "episodes",
        sa.Column(
            "archive_status",
            sa.String(length=32),
            nullable=False,
            server_default="none",
        ),
    )
    op.add_column(
        "episodes",
        sa.Column(
            "archive_path",
            sa.String(length=512),
            nullable=True,
        ),
    )
    op.add_column(
        "episodes",
        sa.Column(
            "archive_error",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("episodes", "archive_error")
    op.drop_column("episodes", "archive_path")
    op.drop_column("episodes", "archive_status")
    op.drop_column("podcast_feeds", "archive")
