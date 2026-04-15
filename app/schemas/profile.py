from __future__ import annotations

from datetime import UTC, datetime

from pydantic import AwareDatetime, BaseModel, field_validator


class ProfilePageContext(BaseModel):
    nickname: str
    email: str
    picture_url: str | None
    language_preference: str
    created_at: AwareDatetime
    updated_at: AwareDatetime
    accessed_at: AwareDatetime

    @field_validator("created_at", "updated_at", "accessed_at", mode="before")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
