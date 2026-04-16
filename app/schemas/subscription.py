from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, RootModel, field_validator

from app.core.security import (
    sanitize_subscription_url,
    validate_jsonp_callback,
    validate_since_timestamp,
    validate_subscription_format,
)


class SubscriptionItem(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    mygpo_link: str | None = None


class SubscriptionJsonUploadItem(BaseModel):
    url: str


class SubscriptionJsonUpload(RootModel[list[str] | list[SubscriptionJsonUploadItem]]):
    def to_urls(self) -> list[str]:
        values = self.root
        urls: list[str] = []
        for value in values:
            if isinstance(value, str):
                urls.append(value)
            else:
                urls.append(value.url)
        return urls


class SubscriptionReadQuery(BaseModel):
    format: str
    jsonp: str | None = None

    @field_validator("format")
    @classmethod
    def validate_format_field(cls, value: str) -> str:
        return validate_subscription_format(value)

    @field_validator("jsonp")
    @classmethod
    def validate_jsonp_field(cls, value: str | None) -> str | None:
        return validate_jsonp_callback(value)


class SubscriptionChangesQuery(BaseModel):
    since: int | None = None

    @field_validator("since")
    @classmethod
    def validate_since(cls, value: int | None) -> int | None:
        return validate_since_timestamp(value)


class SubscriptionDeltaRequest(BaseModel):
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)


class SubscriptionDeltaResponse(BaseModel):
    add: list[str]
    remove: list[str]
    timestamp: int = Field(ge=0)


class SubscriptionDeltaUploadResponse(BaseModel):
    timestamp: int = Field(ge=0)
    update_urls: list[tuple[str, str]]


class NormalizedSubscriptionUrl(BaseModel):
    original: str
    sanitized: str

    @field_validator("sanitized")
    @classmethod
    def validate_sanitized(cls, value: str) -> str:
        return sanitize_subscription_url(value) if value else ""


class SubscriptionRenderPayload(BaseModel):
    items: list[SubscriptionItem]
    format: str
    jsonp: str | None = None

    @field_validator("format")
    @classmethod
    def validate_render_format(cls, value: str) -> str:
        return validate_subscription_format(value)

    @field_validator("jsonp")
    @classmethod
    def validate_render_jsonp(cls, value: str | None) -> str | None:
        return validate_jsonp_callback(value)


class SubscriptionRenderResult(BaseModel):
    media_type: str
    content: Any
