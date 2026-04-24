from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.device import DeviceModel
    from app.db.models.podcast import (
        EpisodeActionEventModel,
        EpisodeActionModel,
        FavoriteEpisodeModel,
        FavoritePodcastModel,
        PodcastListModel,
    )
    from app.db.models.session import AuthenticatedSessionModel
    from app.db.models.settings import (
        AccountSettingModel,
        DeviceSettingModel,
        EpisodeSettingModel,
        PodcastSettingModel,
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    password_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    picture_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    language_preference: Mapped[str] = mapped_column(String(8), nullable=False)
    centralize_sync: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
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
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    devices: Mapped[list[DeviceModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    episode_actions: Mapped[list[EpisodeActionModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    favorite_episodes: Mapped[list[FavoriteEpisodeModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    favorite_podcasts: Mapped[list[FavoritePodcastModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    episode_action_events: Mapped[list[EpisodeActionEventModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    podcast_lists: Mapped[list[PodcastListModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    account_settings: Mapped[AccountSettingModel | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    device_settings: Mapped[list[DeviceSettingModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    podcast_settings: Mapped[list[PodcastSettingModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    episode_settings: Mapped[list[EpisodeSettingModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list[AuthenticatedSessionModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
