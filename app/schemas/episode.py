from __future__ import annotations

from datetime import UTC, datetime

from pydantic import AwareDatetime, BaseModel, Field, field_validator, model_validator

from app.core.security import (
    validate_device_id,
    validate_episode_action,
    validate_episode_progress,
    validate_episode_query_url,
    validate_since_timestamp,
)


class EpisodeActionInput(BaseModel):
    podcast: str
    episode: str
    device: str | None = None
    action: str
    timestamp: AwareDatetime | None = None
    started: int | None = Field(default=None, ge=0)
    position: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)

    @field_validator("started", "position", "total", mode="before")
    @classmethod
    def coerce_negative_to_none(cls, value: object) -> object:
        # AntennaPod sends -1 as sentinel for "unknown/not tracked"
        if isinstance(value, int) and value < 0:
            return None
        return value

    @field_validator("device")
    @classmethod
    def validate_device_field(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_device_id(value)

    @field_validator("action")
    @classmethod
    def validate_action_field(cls, value: str) -> str:
        return validate_episode_action(value)

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_timestamp_timezone(
        cls, value: datetime | str | None
    ) -> datetime | str | None:
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        if isinstance(value, str) and not value.endswith("Z"):
            has_offset = "+" in value or value.count("-") > 2
            if not has_offset:
                return value + "Z"
        return value

    @model_validator(mode="after")
    def validate_progress_fields(self) -> EpisodeActionInput:
        (
            self.started,
            self.position,
            self.total,
        ) = validate_episode_progress(
            action=self.action,
            started=self.started,
            position=self.position,
            total=self.total,
        )
        return self


class EpisodeActionOutput(BaseModel):
    podcast: str
    episode: str
    device: str | None = None
    action: str
    timestamp: AwareDatetime
    started: int | None = Field(default=None, ge=0)
    position: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)

    @field_validator("action")
    @classmethod
    def validate_action_field(cls, value: str) -> str:
        return validate_episode_action(value)

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class EpisodeActionQuery(BaseModel):
    podcast: str | None = None
    device: str | None = None
    since: int | None = None
    aggregated: bool = False

    @field_validator("podcast")
    @classmethod
    def validate_podcast(cls, value: str | None) -> str | None:
        return validate_episode_query_url(value, field_name="podcast")

    @field_validator("device")
    @classmethod
    def validate_device_field(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_device_id(value)

    @field_validator("since")
    @classmethod
    def validate_since(cls, value: int | None) -> int | None:
        return validate_since_timestamp(value)


class EpisodeActionUploadResponse(BaseModel):
    timestamp: int = Field(ge=0)
    update_urls: list[tuple[str, str]]


class EpisodeActionQueryResponse(BaseModel):
    actions: list[EpisodeActionOutput]
    timestamp: int = Field(ge=0)
