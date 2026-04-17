from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.deps import get_auth_service, get_favorites_service
from app.schemas.auth import AuthErrorResponse
from app.schemas.favorite import FavoriteEpisodeItem
from app.services.auth import AuthError, AuthService
from app.services.favorites import FavoritesError, FavoritesService

if TYPE_CHECKING:
    from app.db.models.user import UserModel

router = APIRouter(prefix="/api/2", tags=["Favorites API"])
security = HTTPBasic(auto_error=False)

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
FavoritesServiceDep = Annotated[FavoritesService, Depends(get_favorites_service)]


def build_unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="authentication required",
        headers={"WWW-Authenticate": "Basic"},
    )


async def authenticate_basic_user(
    auth_service: AuthService,
    credentials: HTTPBasicCredentials | None,
) -> UserModel:
    if credentials is None:
        raise build_unauthorized_error()

    try:
        return await auth_service.authenticate_username(
            credentials.username,
            credentials.password,
        )
    except AuthError as exc:
        if exc.code == "invalid_login":
            raise build_unauthorized_error() from exc
        raise


@router.get(
    "/favorites/{username}.json",
    response_model=list[FavoriteEpisodeItem],
    responses={
        401: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        404: {"model": AuthErrorResponse},
    },
)
async def get_favorites(
    username: str,
    auth_service: AuthServiceDep,
    favorites_service: FavoritesServiceDep,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> JSONResponse:
    user = await authenticate_basic_user(auth_service, credentials)
    try:
        favorites = await favorites_service.list_favorites(user, username=username)
    except FavoritesError as exc:
        if exc.code == "forbidden":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="authenticated user does not match requested username",
            ) from exc
        if exc.code == "target_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="target_not_found",
            ) from exc
        raise
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=[item.model_dump(mode="json") for item in favorites],
    )
