"""create device sync groups

Revision ID: 0009_device_sync_groups
Revises: 0008_favorite_episodes
Create Date: 2026-04-18
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0009_device_sync_groups"
down_revision = "0008_favorite_episodes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "device_sync_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
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
            name=op.f("fk_device_sync_groups_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_device_sync_groups")),
    )
    op.create_index(
        "ix_device_sync_groups_user_id",
        "device_sync_groups",
        ["user_id"],
    )

    op.add_column(
        "devices",
        sa.Column("sync_group_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_devices_sync_group_id_device_sync_groups"),
        "devices",
        "device_sync_groups",
        ["sync_group_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_devices_user_id_sync_group_id",
        "devices",
        ["user_id", "sync_group_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_devices_user_id_sync_group_id", table_name="devices")
    op.drop_constraint(
        op.f("fk_devices_sync_group_id_device_sync_groups"),
        "devices",
        type_="foreignkey",
    )
    op.drop_column("devices", "sync_group_id")

    op.drop_index("ix_device_sync_groups_user_id", table_name="device_sync_groups")
    op.drop_table("device_sync_groups")
