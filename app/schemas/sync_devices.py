from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import validate_device_id


class SyncDevicesMutation(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    synchronize: list[list[str]] = Field(default_factory=list)
    stop_synchronize: list[str] = Field(default_factory=list, alias="stop-synchronize")

    @field_validator("synchronize")
    @classmethod
    def validate_synchronize(cls, value: list[list[str]]) -> list[list[str]]:
        normalized: list[list[str]] = []
        for group in value:
            unique: list[str] = []
            seen: set[str] = set()
            for raw in group:
                cleaned = validate_device_id(raw)
                if cleaned in seen:
                    continue
                seen.add(cleaned)
                unique.append(cleaned)
            if len(unique) < 2:
                raise ValueError("synchronize groups must contain at least 2 devices")
            normalized.append(unique)
        return normalized

    @field_validator("stop_synchronize")
    @classmethod
    def validate_stop_synchronize(cls, value: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for raw in value:
            cleaned = validate_device_id(raw)
            if cleaned in seen:
                continue
            seen.add(cleaned)
            unique.append(cleaned)
        return unique


class SyncDevicesStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    synchronized: list[list[str]]
    not_synchronized: list[str] = Field(
        default_factory=list,
        alias="not-synchronized",
        serialization_alias="not-synchronized",
    )
