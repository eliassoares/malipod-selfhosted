from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.device_sync_group import DeviceSyncGroupModel
    from app.db.models.podcast import (
        DeviceSubscriptionModel,
        EpisodeActionModel,
        SubscriptionChangeEventModel,
    )
    from app.db.models.settings import DeviceSettingModel
    from app.db.models.user import UserModel


class DeviceModel(Base):
    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_devices_user_id_device_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    caption: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    device_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sync_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("device_sync_groups.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user: Mapped[UserModel] = relationship(back_populates="devices")
    sync_group: Mapped[DeviceSyncGroupModel | None] = relationship(
        back_populates="devices",
    )
    subscriptions: Mapped[list[DeviceSubscriptionModel]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )
    episode_actions: Mapped[list[EpisodeActionModel]] = relationship(
        back_populates="device",
    )
    subscription_events: Mapped[list[SubscriptionChangeEventModel]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )
    settings_documents: Mapped[list[DeviceSettingModel]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )
