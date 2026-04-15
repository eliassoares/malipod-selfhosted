from __future__ import annotations

from urllib.parse import urlsplit

from pydantic import AwareDatetime, BaseModel, field_validator, model_validator

from app.core.localization import (
    DEFAULT_LOCALE_CODE,
    is_supported_locale,
    normalize_locale,
)
from app.core.security import validate_email_address, validate_nickname


class RegistrationInput(BaseModel):
    nickname: str
    email: str
    password: str
    password_confirmation: str
    picture_url: str | None = None
    language_preference: str = DEFAULT_LOCALE_CODE

    @field_validator("nickname")
    @classmethod
    def validate_nickname_field(cls, value: str) -> str:
        return validate_nickname(value)

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, value: str) -> str:
        return validate_email_address(value)

    @field_validator("picture_url")
    @classmethod
    def validate_picture_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("picture_url must be a valid http or https URL")
        return value.strip()

    @field_validator("language_preference")
    @classmethod
    def validate_language(cls, value: str) -> str:
        normalized = normalize_locale(value)
        if not is_supported_locale(normalized):
            raise ValueError("language_preference must be supported")
        return normalized or DEFAULT_LOCALE_CODE

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> RegistrationInput:
        if self.password != self.password_confirmation:
            raise ValueError("passwords must match")
        if len(self.password) < 8:
            raise ValueError("password must contain at least 8 characters")
        return self


class LoginInput(BaseModel):
    identifier: str
    password: str

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("identifier must not be empty")
        return cleaned


class ApiSessionResponse(BaseModel):
    username: str
    status: str


class AuthErrorResponse(BaseModel):
    detail: str


class SessionContext(BaseModel):
    session_id: str
    username: str
    expires_at: AwareDatetime
