from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import AwareDatetime, BaseModel, Field, field_validator

from app.core.security import validate_device_id, validate_since_timestamp

DEVICE_TYPES = ("desktop", "laptop", "mobile", "server", "other")
EPISODE_STATUSES = ("new", "play", "download", "delete")


class DeviceMutationPayload(BaseModel):
    caption: str | None = None
    type: str | None = None

    @field_validator("caption")
    @classmethod
    def normalize_caption(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in DEVICE_TYPES:
            raise ValueError(
                "type must be one of desktop, laptop, mobile, server, other"
            )
        return cleaned


class DeviceUpsertRequest(DeviceMutationPayload):
    device_id: str

    @field_validator("device_id")
    @classmethod
    def validate_device_id_field(cls, value: str) -> str:
        return validate_device_id(value)


class DeviceSummary(BaseModel):
    id: str
    caption: str
    type: str
    subscriptions: int = Field(ge=0)


class DeviceUpdatesQuery(BaseModel):
    since: int | None = None
    include_actions: bool = False

    @field_validator("since")
    @classmethod
    def validate_since(cls, value: int | None) -> int | None:
        return validate_since_timestamp(value)


class SubscriptionAdd(BaseModel):
    title: str
    url: str
    description: str | None = None
    subscribers: int = Field(default=1, ge=0)
    logo_url: str | None = None
    website: str | None = None
    mygpo_link: str | None = None


class EpisodeUpdate(BaseModel):
    title: str
    url: str
    podcast_title: str
    podcast_url: str
    description: str | None = None
    website: str | None = None
    mygpo_link: str | None = None
    released: AwareDatetime
    status: str
    action: dict[str, Any] | None = None

    @field_validator("released", mode="before")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in EPISODE_STATUSES:
            raise ValueError("status must be one of new, play, download, delete")
        return cleaned


class DeviceUpdatesResponse(BaseModel):
    add: list[SubscriptionAdd]
    remove: list[str]
    updates: list[EpisodeUpdate]
    timestamp: int = Field(ge=0)
