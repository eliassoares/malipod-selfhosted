from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.localization import DEFAULT_LOCALE_CODE, SUPPORTED_LOCALE_CODES
from app.core.security import validate_secret_key


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )

    app_name: str = Field(default="Malipod Selfhosted")
    environment: Literal["local", "test", "production"] = Field(default="local")
    database_url: str
    test_database_url: str = Field(default="sqlite+aiosqlite:///./test.db")
    secret_key: str
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"]
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    session_cookie_name: str = Field(default="sessionid")
    session_ttl_seconds: int = Field(default=1_209_600)
    base_url: str = Field(default="http://localhost:8000")
    default_locale: str = Field(default=DEFAULT_LOCALE_CODE)
    supported_locales: list[str] = Field(
        default_factory=lambda: list(SUPPORTED_LOCALE_CODES)
    )
    archive_dir: str = Field(default="archive")
    archive_workers: int = Field(default=2)
    archive_sync_interval_minutes: int = Field(default=60)

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

    @field_validator("supported_locales", mode="before")
    @classmethod
    def parse_supported_locales(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("supported_locales must be a comma-separated string or a list")

    @field_validator("session_cookie_name")
    @classmethod
    def validate_cookie_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("session_cookie_name must not be empty")
        return value.strip()

    @field_validator("session_ttl_seconds")
    @classmethod
    def validate_session_ttl(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("session_ttl_seconds must be greater than zero")
        return value

    @field_validator("archive_dir")
    @classmethod
    def validate_archive_dir(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("archive_dir must not be empty")
        return value.strip()

    @field_validator("archive_workers")
    @classmethod
    def validate_archive_workers(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("archive_workers must be greater than zero")
        return value

    @field_validator("archive_sync_interval_minutes")
    @classmethod
    def validate_archive_sync_interval_minutes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("archive_sync_interval_minutes must be greater than zero")
        return value

    @field_validator("default_locale")
    @classmethod
    def validate_default_locale(cls, value: str) -> str:
        if value not in SUPPORTED_LOCALE_CODES:
            raise ValueError("default_locale must be one of the supported locales")
        return value

    @model_validator(mode="after")
    def validate_runtime_rules(self) -> Settings:
        if self.environment == "production" and not self.allowed_hosts:
            raise ValueError("allowed_hosts must not be empty in production")
        invalid_locales = [
            locale
            for locale in self.supported_locales
            if locale not in SUPPORTED_LOCALE_CODES
        ]
        if invalid_locales:
            raise ValueError(
                "supported_locales contains unsupported values: "
                + ", ".join(sorted(invalid_locales))
            )
        if self.default_locale not in self.supported_locales:
            raise ValueError("default_locale must be present in supported_locales")
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
