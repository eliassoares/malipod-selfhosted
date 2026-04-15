"""create device sync entities

Revision ID: 0003_device_sync_entities
Revises: 0002_user_auth_entities
Create Date: 2026-04-15
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003_device_sync_entities"
down_revision = "0002_user_auth_entities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("caption", sa.String(length=255), nullable=False),
        sa.Column("device_type", sa.String(length=32), nullable=False),
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
            name=op.f("fk_devices_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_devices")),
        sa.UniqueConstraint(
            "user_id",
            "device_id",
            name="uq_devices_user_id_device_id",
        ),
    )
    op.create_table(
        "podcast_feeds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feed_url", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("mygpo_link", sa.String(length=512), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_podcast_feeds")),
        sa.UniqueConstraint("feed_url", name=op.f("uq_podcast_feeds_feed_url")),
    )
    op.create_table(
        "device_subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_pk", sa.Integer(), nullable=False),
        sa.Column("feed_id", sa.Integer(), nullable=False),
        sa.Column("subscribed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_pk"],
            ["devices.id"],
            name=op.f("fk_device_subscriptions_device_pk_devices"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["feed_id"],
            ["podcast_feeds.id"],
            name=op.f("fk_device_subscriptions_feed_id_podcast_feeds"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_device_subscriptions")),
        sa.UniqueConstraint(
            "device_pk",
            "feed_id",
            name="uq_device_subscriptions_device_pk_feed_id",
        ),
    )
    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feed_id", sa.Integer(), nullable=False),
        sa.Column("episode_url", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("website", sa.String(length=512), nullable=True),
        sa.Column("mygpo_link", sa.String(length=512), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=False),
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
            name=op.f("fk_episodes_feed_id_podcast_feeds"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_episodes")),
        sa.UniqueConstraint("episode_url", name=op.f("uq_episodes_episode_url")),
    )
    op.create_table(
        "episode_actions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_pk", sa.Integer(), nullable=True),
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("action", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_pk"],
            ["devices.id"],
            name=op.f("fk_episode_actions_device_pk_devices"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["episode_id"],
            ["episodes.id"],
            name=op.f("fk_episode_actions_episode_id_episodes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_episode_actions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_episode_actions")),
        sa.UniqueConstraint(
            "user_id",
            "episode_id",
            name="uq_episode_actions_user_id_episode_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("episode_actions")
    op.drop_table("episodes")
    op.drop_table("device_subscriptions")
    op.drop_table("podcast_feeds")
    op.drop_table("devices")
