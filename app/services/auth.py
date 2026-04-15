from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import selectinload

from app.core.localization import DEFAULT_LOCALE_CODE, normalize_locale
from app.core.security import (
    derive_password_hash,
    generate_session_token,
    validate_email_address,
    validate_nickname,
    verify_password,
)
from app.db.models.session import AuthenticatedSessionModel
from app.db.models.user import UserModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings
    from app.schemas.auth import LoginInput, RegistrationInput


class AuthError(Exception):
    def __init__(
        self,
        code: Literal["invalid_login", "user_exists", "profile_forbidden"],
    ) -> None:
        self.code = code
        super().__init__(code)


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def _fetch_user(
        self, statement: Select[tuple[UserModel]]
    ) -> UserModel | None:
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_nickname(self, nickname: str) -> UserModel | None:
        try:
            normalized = validate_nickname(nickname)
        except ValueError:
            return None
        return await self._fetch_user(
            select(UserModel).where(
                UserModel.nickname == normalized,
                UserModel.deactivated_at.is_(None),
            )
        )

    async def get_user_by_email(self, email: str) -> UserModel | None:
        normalized = validate_email_address(email)
        return await self._fetch_user(
            select(UserModel).where(
                UserModel.email == normalized,
                UserModel.deactivated_at.is_(None),
            )
        )

    async def create_user(self, payload: RegistrationInput) -> UserModel:
        existing = await self.session.execute(
            select(UserModel).where(
                or_(
                    UserModel.nickname == payload.nickname,
                    UserModel.email == payload.email,
                ),
                UserModel.deactivated_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise AuthError("user_exists")

        password_hash, password_salt = derive_password_hash(payload.password)
        user = UserModel(
            nickname=payload.nickname,
            password_hash=password_hash,
            password_salt=password_salt,
            email=payload.email,
            picture_url=payload.picture_url,
            language_preference=payload.language_preference,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate_identifier(self, payload: LoginInput) -> UserModel:
        identifier = payload.identifier.strip()
        statement = select(UserModel).where(UserModel.deactivated_at.is_(None))
        if "@" in identifier:
            statement = statement.where(
                UserModel.email == validate_email_address(identifier)
            )
        else:
            statement = statement.where(UserModel.nickname == identifier)

        user = await self._fetch_user(statement)
        if user is None or not verify_password(
            payload.password, user.password_hash, user.password_salt
        ):
            raise AuthError("invalid_login")

        user.accessed_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate_username(self, username: str, password: str) -> UserModel:
        user = await self.get_user_by_nickname(username)
        if user is None or not verify_password(
            password, user.password_hash, user.password_salt
        ):
            raise AuthError("invalid_login")
        user.accessed_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_session(
        self, user: UserModel, user_agent: str | None
    ) -> AuthenticatedSessionModel:
        session_model = AuthenticatedSessionModel(
            session_id=generate_session_token(),
            user_id=user.id,
            expires_at=datetime.now(UTC)
            + timedelta(seconds=self.settings.session_ttl_seconds),
            user_agent=user_agent[:255] if user_agent else None,
        )
        self.session.add(session_model)
        await self.session.commit()
        await self.session.refresh(session_model)
        return session_model

    async def get_active_session(
        self, session_id: str | None
    ) -> AuthenticatedSessionModel | None:
        if session_id is None:
            return None
        result = await self.session.execute(
            select(AuthenticatedSessionModel)
            .options(selectinload(AuthenticatedSessionModel.user))
            .join(AuthenticatedSessionModel.user)
            .where(
                AuthenticatedSessionModel.session_id == session_id,
                AuthenticatedSessionModel.revoked_at.is_(None),
                AuthenticatedSessionModel.expires_at > datetime.now(UTC),
                UserModel.deactivated_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_session(self, session_model: AuthenticatedSessionModel) -> None:
        session_model.revoked_at = datetime.now(UTC)
        await self.session.commit()

    async def sync_user_locale(self, user: UserModel, locale: str) -> UserModel:
        user.language_preference = normalize_locale(locale) or DEFAULT_LOCALE_CODE
        user.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(user)
        return user
