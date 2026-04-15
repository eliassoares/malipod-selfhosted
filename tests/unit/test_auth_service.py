from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.schemas.auth import LoginInput, RegistrationInput
from app.services.auth import AuthError, AuthService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings


def build_registration() -> RegistrationInput:
    return RegistrationInput(
        nickname="listener_1",
        email="listener@example.com",
        password="supersecret",
        password_confirmation="supersecret",
        picture_url="https://example.com/avatar.png",
        language_preference="en",
    )


@pytest.mark.asyncio
async def test_auth_service_creates_and_authenticates_user(
    db_session: AsyncSession, settings: Settings
) -> None:
    service = AuthService(db_session, settings)
    user = await service.create_user(build_registration())

    assert user.nickname == "listener_1"

    authenticated = await service.authenticate_identifier(
        LoginInput(identifier="listener@example.com", password="supersecret")
    )
    assert authenticated.id == user.id


@pytest.mark.asyncio
async def test_auth_service_rejects_duplicate_user(
    db_session: AsyncSession, settings: Settings
) -> None:
    service = AuthService(db_session, settings)
    await service.create_user(build_registration())

    with pytest.raises(AuthError, match="user_exists"):
        await service.create_user(build_registration())


@pytest.mark.asyncio
async def test_auth_service_rejects_invalid_login(
    db_session: AsyncSession, settings: Settings
) -> None:
    service = AuthService(db_session, settings)
    await service.create_user(build_registration())

    with pytest.raises(AuthError, match="invalid_login"):
        await service.authenticate_identifier(
            LoginInput(identifier="listener@example.com", password="wrongpass")
        )


@pytest.mark.asyncio
async def test_auth_service_creates_and_revokes_session(
    db_session: AsyncSession, settings: Settings
) -> None:
    service = AuthService(db_session, settings)
    user = await service.create_user(build_registration())

    session_model = await service.create_session(user, "pytest")
    active = await service.get_active_session(session_model.session_id)

    assert active is not None
    assert active.user.nickname == "listener_1"

    await service.revoke_session(active)
    revoked = await service.get_active_session(session_model.session_id)

    assert revoked is None
