from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClientConfigService(BaseModel):
    baseurl: str

    @field_validator("baseurl")
    @classmethod
    def validate_baseurl(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("baseurl must not be empty")
        if not cleaned.endswith("/"):
            raise ValueError("baseurl must end with '/'")
        return cleaned


class ClientConfigResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mygpo: ClientConfigService
    mygpo_feedservice: ClientConfigService = Field(alias="mygpo-feedservice")
    update_timeout: int

    @field_validator("update_timeout")
    @classmethod
    def validate_update_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("update_timeout must be greater than zero")
        return value
