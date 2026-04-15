from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegistrationInput


def build_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "nickname": "listener_1",
        "email": "listener@example.com",
        "password": "supersecret",
        "password_confirmation": "supersecret",
        "picture_url": "https://example.com/avatar.png",
        "language_preference": "en",
    }
    payload.update(overrides)
    return payload


def test_registration_defaults_to_supported_values() -> None:
    payload = RegistrationInput(**build_payload(language_preference="pt-BR"))
    assert payload.nickname == "listener_1"
    assert payload.language_preference == "pt-BR"


@pytest.mark.parametrize(
    "nickname",
    ["short", "nickname-too-long-123", "bad!name", "space name"],
)
def test_registration_rejects_invalid_nickname(nickname: str) -> None:
    with pytest.raises(ValidationError, match="nickname"):
        RegistrationInput(**build_payload(nickname=nickname))


def test_registration_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError, match="email"):
        RegistrationInput(**build_payload(email="invalid-email"))


def test_registration_requires_matching_passwords() -> None:
    with pytest.raises(ValidationError, match="passwords must match"):
        RegistrationInput(
            **build_payload(password="supersecret", password_confirmation="otherpass")
        )


def test_registration_rejects_invalid_picture_url() -> None:
    with pytest.raises(ValidationError, match="picture_url"):
        RegistrationInput(**build_payload(picture_url="ftp://example.com/avatar.png"))
