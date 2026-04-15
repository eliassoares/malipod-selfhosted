from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.security import validate_secret_key


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )

    app_name: str = Field(default="Malipod")
    environment: Literal["local", "test", "production"] = Field(default="local")
    database_url: str
    test_database_url: str = Field(default="sqlite+aiosqlite:///./test.db")
    secret_key: str
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("allowed_hosts must be a comma-separated string or a list")

    @field_validator("secret_key")
    @classmethod
    def validate_secret(cls, value: str) -> str:
        validate_secret_key(value)
        return value

    @model_validator(mode="after")
    def validate_runtime_rules(self) -> Settings:
        if self.environment == "production" and not self.allowed_hosts:
            raise ValueError("allowed_hosts must not be empty in production")
        return self

    @property
    def effective_database_url(self) -> str:
        if self.environment == "test":
            return self.test_database_url
        return self.database_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def clear_settings_cache() -> None:
    get_settings.cache_clear()
