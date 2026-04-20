from __future__ import annotations

from datetime import UTC, datetime

from pydantic import AwareDatetime, BaseModel, Field, field_validator


class PodcastDirectoryItem(BaseModel):
    url: str
    title: str
    author: str | None = None
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
