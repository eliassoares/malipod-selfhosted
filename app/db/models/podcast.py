from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.placeholders import choose_placeholder_url_random
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.device import DeviceModel
    from app.db.models.settings import EpisodeSettingModel, PodcastSettingModel
    from app.db.models.user import UserModel


class PodcastFeedModel(Base):
    __tablename__ = "podcast_feeds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    feed_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        default=choose_placeholder_url_random,
        server_default="/static/placeholders/lilith.png",
    )
    mygpo_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
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
    list_items: Mapped[list[PodcastListItemModel]] = relationship(
        back_populates="feed",
        cascade="save-update, merge, delete",
        passive_deletes=True,
    )
    episodes: Mapped[list[EpisodeModel]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan",
    )
    podcast_settings: Mapped[list[PodcastSettingModel]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan",
    )
    favorited_by: Mapped[list[FavoritePodcastModel]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan",
    )


class PodcastListModel(Base):
    __tablename__ = "podcast_lists"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_podcast_lists_user_id_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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

    user: Mapped[UserModel] = relationship(back_populates="podcast_lists")
    items: Mapped[list[PodcastListItemModel]] = relationship(
        back_populates="podcast_list",
        cascade="all, delete-orphan",
        order_by="PodcastListItemModel.position",
    )


class PodcastListItemModel(Base):
    __tablename__ = "podcast_list_items"
    __table_args__ = (
        UniqueConstraint(
            "list_id",
            "feed_id",
            name="uq_podcast_list_items_list_id_feed_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("podcast_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    feed_id: Mapped[int] = mapped_column(
        ForeignKey("podcast_feeds.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
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

    podcast_list: Mapped[PodcastListModel] = relationship(back_populates="items")
    feed: Mapped[PodcastFeedModel] = relationship(back_populates="list_items")


class EpisodePlaylistModel(Base):
    __tablename__ = "episode_playlists"
    __table_args__ = (
        UniqueConstraint("user_id", "title", name="uq_episode_playlists_user_id_title"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
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

    user: Mapped[UserModel] = relationship(back_populates="episode_playlists")
    items: Mapped[list[EpisodePlaylistItemModel]] = relationship(
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="EpisodePlaylistItemModel.created_at",
    )


class EpisodePlaylistItemModel(Base):
    __tablename__ = "episode_playlist_items"
    __table_args__ = (
        UniqueConstraint(
            "playlist_id",
            "episode_id",
            name="uq_episode_playlist_items_playlist_id_episode_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("episode_playlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    episode_id: Mapped[int] = mapped_column(
        ForeignKey("episodes.id", ondelete="CASCADE"),
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

    playlist: Mapped[EpisodePlaylistModel] = relationship(back_populates="items")
    episode: Mapped[EpisodeModel] = relationship(back_populates="playlist_items")


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
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mygpo_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        default=choose_placeholder_url_random,
        server_default="/static/placeholders/lilith.png",
    )
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
    settings_documents: Mapped[list[EpisodeSettingModel]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
    )
    favorites: Mapped[list[FavoriteEpisodeModel]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
    )
    playlist_items: Mapped[list[EpisodePlaylistItemModel]] = relationship(
        back_populates="episode",
        cascade="save-update, merge, delete",
        passive_deletes=True,
    )


class FavoritePodcastModel(Base):
    __tablename__ = "favorite_podcasts"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "feed_id",
            name="uq_favorite_podcasts_user_id_feed_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    feed_id: Mapped[int] = mapped_column(
        ForeignKey("podcast_feeds.id", ondelete="CASCADE"),
        nullable=False,
    )
    favorited_at: Mapped[datetime] = mapped_column(
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

    user: Mapped[UserModel] = relationship(back_populates="favorite_podcasts")
    feed: Mapped[PodcastFeedModel] = relationship(back_populates="favorited_by")


class FavoriteEpisodeModel(Base):
    __tablename__ = "favorite_episodes"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "episode_id",
            name="uq_favorite_episodes_user_id_episode_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    episode_id: Mapped[int] = mapped_column(
        ForeignKey("episodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    favorited_at: Mapped[datetime] = mapped_column(
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

    user: Mapped[UserModel] = relationship(back_populates="favorite_episodes")
    episode: Mapped[EpisodeModel] = relationship(back_populates="favorites")


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
