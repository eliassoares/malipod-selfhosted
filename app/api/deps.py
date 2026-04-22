from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import Settings, get_settings
from app.core.security import verify_password
from app.db.session import get_db_session
from app.services.auth import AuthError, AuthService
from app.services.devices import DeviceService
from app.services.directory import DirectoryService
from app.services.episodes import EpisodeService
from app.services.favorites import FavoritesService
from app.services.localization import LocalizationService
from app.services.podcast_detail import PodcastDetailService
from app.services.podcast_favorites import PodcastFavoritesService
from app.services.podcast_lists import PodcastListService
from app.services.readiness import ReadinessService
from app.services.settings import SettingsService
from app.services.subscriptions import SubscriptionService
from app.services.subscriptions_page import SubscriptionsPageService
from app.services.sync_devices import SyncDevicesService
from app.services.user_data_tools import UserDataToolsService

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


def get_directory_service(
    session: Annotated[Any, Depends(get_request_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> DirectoryService:
    return DirectoryService(session=session, settings=settings)


def get_favorites_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> FavoritesService:
    return FavoritesService(session=session)


def get_sync_devices_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> SyncDevicesService:
    return SyncDevicesService(session=session)


def get_podcast_list_service(
    session: Annotated[Any, Depends(get_request_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> PodcastListService:
    return PodcastListService(session=session, base_url=settings.base_url)


def get_podcast_favorites_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> PodcastFavoritesService:
    return PodcastFavoritesService(session=session)


def get_podcast_detail_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> PodcastDetailService:
    return PodcastDetailService(session=session)


def get_settings_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> SettingsService:
    return SettingsService(session=session)


def get_localization_service(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> LocalizationService:
    return LocalizationService(settings=settings)


def get_subscriptions_page_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> SubscriptionsPageService:
    return SubscriptionsPageService(session=session)


def get_user_data_tools_service(
    session: Annotated[Any, Depends(get_request_session)],
) -> UserDataToolsService:
    return UserDataToolsService(session=session)


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


basic_security = HTTPBasic(auto_error=False)


async def get_required_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: Annotated[HTTPBasicCredentials | None, Depends(basic_security)],
) -> UserModel:
    session_id = request.cookies.get(settings.session_cookie_name)
    if session_id:
        session_model = await auth_service.get_active_session(session_id)
        if session_model is not None:
            return session_model.user

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    user = await auth_service.get_user_by_nickname(credentials.username)
    if user is None or not verify_password(
        credentials.password, user.password_hash, user.password_salt
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


async def authenticate_api_user(
    username: str,
    request: Request,
    auth_service: AuthService,
    settings: Settings,
    credentials: HTTPBasicCredentials | None,
) -> UserModel:
    session_id = request.cookies.get(settings.session_cookie_name)
    if session_id:
        session_model = await auth_service.get_active_session(session_id)
        if session_model is not None:
            if session_model.user.nickname != username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="authenticated user does not match requested username",
                )
            return session_model.user

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    try:
        authenticated = await auth_service.authenticate_username(
            credentials.username,
            credentials.password,
        )
    except AuthError as exc:
        if exc.code == "invalid_login":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="authentication required",
                headers={"WWW-Authenticate": "Basic"},
            ) from exc
        raise

    if authenticated.nickname != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="authenticated user does not match requested username",
        )
    return authenticated
