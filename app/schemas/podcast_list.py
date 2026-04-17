from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, RootModel, field_validator, model_validator

from app.core.security import (
    normalize_podcast_list_name,
    sanitize_subscription_url,
    validate_list_format,
    validate_podcast_list_title,
)


class PodcastListEntry(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    mygpo_link: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        sanitized = sanitize_subscription_url(value)
        if not sanitized:
            raise ValueError("url must be an http or https URL")
        return sanitized


class PodcastListSummary(BaseModel):
    title: str
    name: str
    web: str


class PodcastListJsonUploadItem(BaseModel):
    url: str
    title: str | None = None
    website: str | None = None
    description: str | None = None


class PodcastListJsonUploadDocument(BaseModel):
    podcasts: list[str | PodcastListJsonUploadItem]


class PodcastListJsonUpload(
    RootModel[list[str | PodcastListJsonUploadItem] | PodcastListJsonUploadDocument]
):
    def to_entries(self) -> list[PodcastListJsonUploadItem]:
        values = self.root
        if isinstance(values, PodcastListJsonUploadDocument):
            raw_items = values.podcasts
        else:
            raw_items = values

        entries: list[PodcastListJsonUploadItem] = []
        for value in raw_items:
            if isinstance(value, str):
                entries.append(PodcastListJsonUploadItem(url=value))
            else:
                entries.append(value)
        return entries


class PodcastListRenderPayload(BaseModel):
    title: str
    name: str
    items: list[PodcastListEntry]
    format: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return validate_podcast_list_title(value)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalize_podcast_list_name(value)

    @field_validator("format")
    @classmethod
    def validate_render_format(cls, value: str) -> str:
        return validate_list_format(value)


class PodcastListRenderResult(BaseModel):
    media_type: str
    content: Any


class PodcastListDocument(BaseModel):
    title: str
    name: str
    podcasts: list[PodcastListEntry]


class PodcastListCreateRequest(BaseModel):
    title: str
    format: str

    @field_validator("title")
    @classmethod
    def validate_title_field(cls, value: str) -> str:
        return validate_podcast_list_title(value)

    @field_validator("format")
    @classmethod
    def validate_format_field(cls, value: str) -> str:
        return validate_list_format(value)


class PodcastListUpdateRequest(BaseModel):
    format: str

    @field_validator("format")
    @classmethod
    def validate_format_field(cls, value: str) -> str:
        return validate_list_format(value)


class PodcastListPathRequest(BaseModel):
    listname: str
    format: str

    @field_validator("listname")
    @classmethod
    def validate_listname(cls, value: str) -> str:
        normalized = normalize_podcast_list_name(value)
        if normalized != value.strip().lower():
            raise ValueError("listname must be a lowercase slug")
        return normalized

    @field_validator("format")
    @classmethod
    def validate_format_field(cls, value: str) -> str:
        return validate_list_format(value)


class PodcastListCreateResponse(BaseModel):
    location: str = Field(min_length=1)


class PodcastListQuery(BaseModel):
    username: str
    listname: str | None = None

    @model_validator(mode="after")
    def validate_list_query(self) -> PodcastListQuery:
        if self.listname is not None:
            self.listname = normalize_podcast_list_name(self.listname)
        return self
