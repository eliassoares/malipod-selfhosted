from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

QueueMode = Literal["playlist", "podcast"]
PlayerAction = Literal["play", "pause", "stop"]


class PlayerStateInput(BaseModel):
    episode_id: int | None = Field(default=None, ge=1)
    position_sec: int | None = Field(default=None, ge=0)
    queue_mode: QueueMode | None = None
    queue_ref_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_state(self) -> PlayerStateInput:
        if self.episode_id is None and any(
            value is not None
            for value in (self.position_sec, self.queue_mode, self.queue_ref_id)
        ):
            raise ValueError("episode_id must be provided when saving player state")
        if self.queue_mode is None and self.queue_ref_id is not None:
            raise ValueError("queue_ref_id requires queue_mode")
        if self.queue_mode is not None and self.queue_ref_id is None:
            raise ValueError("queue_mode requires queue_ref_id")
        return self


class PlayerActionInput(BaseModel):
    episode_id: int = Field(ge=1)
    action: PlayerAction
    started: int | None = Field(default=None, ge=0)
    position: int | None = Field(default=None, ge=0)
    total: int | None = Field(default=None, ge=0)
    timestamp: datetime | None = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_timezone(cls, value: datetime | str | None) -> datetime | str | None:
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        if isinstance(value, str) and not value.endswith("Z"):
            has_offset = "+" in value or value.count("-") > 2
            if not has_offset:
                return value + "Z"
        return value

    @model_validator(mode="after")
    def validate_progress(self) -> PlayerActionInput:
        values = (self.started, self.position, self.total)
        if self.action in {"play", "pause"}:
            if any(value is None for value in values):
                raise ValueError(
                    "play/pause actions require started, position, and total together"
                )
            return self
        if any(value is not None for value in values):
            raise ValueError("progress fields are only valid for play/pause")
        return self


class OkResponse(BaseModel):
    ok: bool = True


class NextEpisodeResponse(BaseModel):
    episode_id: int | None = None


class EpisodeInfoResponse(BaseModel):
    episode_id: int
    feed_id: int
    media_url: str | None = None
    episode_title: str
    podcast_title: str
    cover_url: str | None = None
