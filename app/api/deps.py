from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.services.auth import AuthService
from app.services.devices import DeviceService
from app.services.episodes import EpisodeService
from app.services.localization import LocalizationService
from app.services.readiness import ReadinessService
from app.services.subscriptions import SubscriptionService

if TYPE_CHECKING:
    from app.db.models.user import UserModel


def get_runtime_settings() -> Settings:
    return get_settings()


def get_readiness_service(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> ReadinessService:
    return ReadinessService(settings=settings)


async def get_request_session(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> Any:
    async for session in get_db_session(settings):
        yield session


def get_auth_service(
    session: Annotated[Any, Depends(get_request_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> AuthService:
    return AuthService(session=session, settings=settings)


def get_device_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> DeviceService:
    return DeviceService(session=session)


def get_subscription_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> SubscriptionService:
    return SubscriptionService(session=session)


def get_episode_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> EpisodeService:
    return EpisodeService(session=session)


def get_localization_service(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> LocalizationService:
    return LocalizationService(settings=settings)


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserModel | None:
    session_id = request.cookies.get(settings.session_cookie_name)
    session_model = await auth_service.get_active_session(session_id)
    if session_model is None:
        return None
    return session_model.user
