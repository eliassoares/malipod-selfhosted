from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, RootModel, field_validator, model_validator

from app.core.security import (
    validate_device_id,
    validate_settings_episode_url,
    validate_settings_json_object,
    validate_settings_podcast_url,
    validate_settings_scope,
)

SettingsScope = Literal["account", "device", "podcast", "episode"]


class SettingsScopeQuery(BaseModel):
    scope: SettingsScope
    podcast: str | None = None
    device: str | None = None
    episode: str | None = None

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, value: str) -> str:
        return validate_settings_scope(value)

    @field_validator("device")
    @classmethod
    def validate_device(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_device_id(value)

    @field_validator("podcast")
    @classmethod
    def validate_podcast(cls, value: str | None) -> str | None:
        return validate_settings_podcast_url(value)

    @field_validator("episode")
    @classmethod
    def validate_episode(cls, value: str | None) -> str | None:
        return validate_settings_episode_url(value)

    @model_validator(mode="after")
    def validate_scope_requirements(self) -> SettingsScopeQuery:
        if self.scope == "account":
            return self
        if self.scope == "device" and self.device is None:
            raise ValueError("device scope requires device query parameter")
        if self.scope == "podcast" and self.podcast is None:
            raise ValueError("podcast scope requires podcast query parameter")
        if self.scope == "episode" and (self.podcast is None or self.episode is None):
            raise ValueError(
                "episode scope requires podcast and episode query parameters"
            )
        return self


class SettingsMutationRequest(BaseModel):
    set: dict[str, Any] = {}
    remove: list[str] = []

    @field_validator("set", mode="before")
    @classmethod
    def validate_set(cls, value: Any) -> dict[str, Any]:
        return validate_settings_json_object(value, field_name="set")

    @field_validator("remove")
    @classmethod
    def validate_remove(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("remove must contain only strings")
            key = item.strip()
            if key:
                cleaned.append(key)
        return cleaned


class SettingsDocument(RootModel[dict[str, Any]]):
    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> SettingsDocument:
        return cls(validate_settings_json_object(value, field_name="settings"))
