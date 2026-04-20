from __future__ import annotations

from datetime import UTC, datetime

from pydantic import AwareDatetime, BaseModel, Field, field_validator

from app.core.security import (
    validate_count_parameter,
    validate_settings_episode_url,
    validate_settings_podcast_url,
    validate_subscription_format,
)


class SearchQuery(BaseModel):
    q: str
    format: str

    @field_validator("q")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("q must not be empty")
        return cleaned

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        return validate_subscription_format(value)


class ToplistPathParams(BaseModel):
    number: int = Field(ge=1)
    format: str

    @field_validator("number")
    @classmethod
    def validate_number(cls, value: int) -> int:
        return validate_count_parameter(value, name="number")

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        return validate_subscription_format(value)


class TagsPathParams(BaseModel):
    count: int = Field(ge=1)

    @field_validator("count")
    @classmethod
    def validate_count(cls, value: int) -> int:
        return validate_count_parameter(value, name="count")


class TagPodcastsPathParams(BaseModel):
    tag: str
    count: int = Field(ge=1)

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("tag must not be empty")
        return cleaned

    @field_validator("count")
    @classmethod
    def validate_count(cls, value: int) -> int:
        return validate_count_parameter(value, name="count")


class PodcastDataQuery(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        validated = validate_settings_podcast_url(value)
        if validated is None:
            raise ValueError("url must be an http or https URL")
        return validated


class EpisodeDataQuery(BaseModel):
    podcast: str
    url: str

    @field_validator("podcast")
    @classmethod
    def validate_podcast(cls, value: str) -> str:
        validated = validate_settings_podcast_url(value)
        if validated is None:
            raise ValueError("podcast must be an http or https URL")
        return validated

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        validated = validate_settings_episode_url(value)
        if validated is None:
            raise ValueError("url must be an ASCII http or https URL")
        return validated


class PodcastDirectoryItem(BaseModel):
    url: str
    title: str
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    subscribers: int = Field(ge=0)
    mygpo_link: str


class TagSummary(BaseModel):
    title: str
    tag: str
    usage: int = Field(ge=0)


class PodcastDataResponse(BaseModel):
    url: str
    title: str
    author: str | None = None
    description: str | None = None
    subscribers: int = Field(ge=0)
    logo_url: str | None = None
    website: str | None = None
    mygpo_link: str


class EpisodeDataResponse(BaseModel):
    title: str
    url: str
    podcast_title: str
    podcast_url: str
    description: str | None = None
    website: str | None = None
    released: AwareDatetime
    mygpo_link: str | None = None

    @field_validator("released", mode="before")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
