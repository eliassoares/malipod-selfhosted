from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.device import DeviceModel
    from app.db.models.user import UserModel


class PodcastFeedModel(Base):
    __tablename__ = "podcast_feeds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    feed_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mygpo_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
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

    subscriptions: Mapped[list[DeviceSubscriptionModel]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan",
    )
    episodes: Mapped[list[EpisodeModel]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan",
    )


class DeviceSubscriptionModel(Base):
    __tablename__ = "device_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "device_pk",
            "feed_id",
            name="uq_device_subscriptions_device_pk_feed_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_pk: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    feed_id: Mapped[int] = mapped_column(
        ForeignKey("podcast_feeds.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscribed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    unsubscribed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    device: Mapped[DeviceModel] = relationship(back_populates="subscriptions")
    feed: Mapped[PodcastFeedModel] = relationship(back_populates="subscriptions")


class SubscriptionChangeEventModel(Base):
    __tablename__ = "subscription_change_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_pk: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    feed_url: Mapped[str] = mapped_column(String(512), nullable=False)
    operation: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    device: Mapped[DeviceModel] = relationship(back_populates="subscription_events")


class EpisodeModel(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    feed_id: Mapped[int] = mapped_column(
        ForeignKey("podcast_feeds.id", ondelete="CASCADE"),
        nullable=False,
    )
    episode_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mygpo_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    released_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
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

    feed: Mapped[PodcastFeedModel] = relationship(back_populates="episodes")
    actions: Mapped[list[EpisodeActionModel]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
    )
    action_events: Mapped[list[EpisodeActionEventModel]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
    )


class EpisodeActionModel(Base):
    __tablename__ = "episode_actions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "episode_id",
            name="uq_episode_actions_user_id_episode_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_pk: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    episode_id: Mapped[int] = mapped_column(
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user: Mapped[UserModel] = relationship(back_populates="episode_actions")
    device: Mapped[DeviceModel | None] = relationship(back_populates="episode_actions")
    episode: Mapped[EpisodeModel] = relationship(back_populates="actions")


class EpisodeActionEventModel(Base):
    __tablename__ = "episode_action_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    episode_id: Mapped[int] = mapped_column(
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    podcast_url: Mapped[str] = mapped_column(String(512), nullable=False)
    episode_url: Mapped[str] = mapped_column(String(512), nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    started: Mapped[int | None] = mapped_column(nullable=True)
    position: Mapped[int | None] = mapped_column(nullable=True)
    total: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    user: Mapped[UserModel] = relationship(back_populates="episode_action_events")
    episode: Mapped[EpisodeModel] = relationship(back_populates="action_events")
