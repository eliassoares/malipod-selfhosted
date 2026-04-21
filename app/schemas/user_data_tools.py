from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
)

_http_url_adapter: TypeAdapter[AnyHttpUrl] = TypeAdapter(AnyHttpUrl)


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _validate_http_url(value: str) -> str:
    _http_url_adapter.validate_python(value)
    return value


UtcDatetime = Annotated[datetime, AfterValidator(_ensure_timezone)]
HttpUrlStr = Annotated[str, AfterValidator(_validate_http_url)]


class UserSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nickname: str
    email: str
    picture_url: str | None = None
    language_preference: str
    created_at: UtcDatetime
    updated_at: UtcDatetime
    accessed_at: UtcDatetime
    deactivated_at: UtcDatetime | None = None


class AccountSettingsSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: UtcDatetime
    updated_at: UtcDatetime


class DeviceSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    device_id: str
    caption: str = ""
    device_type: str
    sync_group: str | None = None
    created_at: UtcDatetime
    updated_at: UtcDatetime


class DeviceSettingsSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    device_id: str
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: UtcDatetime
    updated_at: UtcDatetime


class PodcastFeedSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    feed_url: HttpUrlStr
    title: str
    author: str | None = None
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    mygpo_link: str | None = None
    categories: list[str] | None = None
    created_at: UtcDatetime
    updated_at: UtcDatetime


class EpisodeSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    feed_url: HttpUrlStr
    episode_url: HttpUrlStr
    title: str
    description: str | None = None
    website: str | None = None
    mygpo_link: str | None = None
    released_at: UtcDatetime
    created_at: UtcDatetime
    updated_at: UtcDatetime


class DeviceSubscriptionSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    device_id: str
    feed_url: HttpUrlStr
    subscribed_at: UtcDatetime
    unsubscribed_at: UtcDatetime | None = None
    updated_at: UtcDatetime


class EpisodeActionSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    episode_url: HttpUrlStr
    status: str
    action: dict[str, Any] | None = None
    device_id: str | None = None
    occurred_at: UtcDatetime
    updated_at: UtcDatetime


class FavoriteEpisodeSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    episode_url: HttpUrlStr
    favorited_at: UtcDatetime
    created_at: UtcDatetime
    updated_at: UtcDatetime


class SubscriptionChangeEventSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    device_id: str
    feed_url: HttpUrlStr
    operation: str
    created_at: UtcDatetime


class EpisodeActionEventSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    episode_url: HttpUrlStr
    podcast_url: HttpUrlStr
    device_id: str | None = None
    action: str
    occurred_at: UtcDatetime
    started: int | None = None
    position: int | None = None
    total: int | None = None
    created_at: UtcDatetime


class PodcastListSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    name: str
    created_at: UtcDatetime
    updated_at: UtcDatetime


class PodcastListItemSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    list_name: str
    feed_url: HttpUrlStr
    position: int
    created_at: UtcDatetime
    updated_at: UtcDatetime


class PodcastSettingsSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    feed_url: HttpUrlStr
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: UtcDatetime
    updated_at: UtcDatetime


class EpisodeSettingsSnapshotRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    episode_url: HttpUrlStr
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: UtcDatetime
    updated_at: UtcDatetime


class UserDataSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    users: list[UserSnapshotRow] = Field(default_factory=list)
    account_settings: list[AccountSettingsSnapshotRow] = Field(default_factory=list)
    devices: list[DeviceSnapshotRow] = Field(default_factory=list)
    device_settings: list[DeviceSettingsSnapshotRow] = Field(default_factory=list)
    podcast_feeds: list[PodcastFeedSnapshotRow] = Field(default_factory=list)
    episodes: list[EpisodeSnapshotRow] = Field(default_factory=list)
    device_subscriptions: list[DeviceSubscriptionSnapshotRow] = Field(
        default_factory=list
    )
    episode_actions: list[EpisodeActionSnapshotRow] = Field(default_factory=list)
    favorite_episodes: list[FavoriteEpisodeSnapshotRow] = Field(default_factory=list)
    subscription_change_events: list[SubscriptionChangeEventSnapshotRow] = Field(
        default_factory=list
    )
    episode_action_events: list[EpisodeActionEventSnapshotRow] = Field(
        default_factory=list
    )
    podcast_lists: list[PodcastListSnapshotRow] = Field(default_factory=list)
    podcast_list_items: list[PodcastListItemSnapshotRow] = Field(default_factory=list)
    podcast_settings: list[PodcastSettingsSnapshotRow] = Field(default_factory=list)
    episode_settings: list[EpisodeSettingsSnapshotRow] = Field(default_factory=list)
