from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_runtime_settings
from app.schemas.client_config import ClientConfigResponse, ClientConfigService

if TYPE_CHECKING:
    from app.core.config import Settings

router = APIRouter(tags=["Client Config"])

SettingsDep = Annotated["Settings", Depends(get_runtime_settings)]

DEFAULT_UPDATE_TIMEOUT_SECONDS = 86_400


def normalize_base_url(base_url: str) -> str:
    cleaned = base_url.strip()
    return f"{cleaned.rstrip('/')}/"


@router.get("/clientconfig.json", response_model=ClientConfigResponse)
async def client_config(settings: SettingsDep) -> ClientConfigResponse:
    baseurl = normalize_base_url(settings.base_url)
    return ClientConfigResponse.model_validate(
        {
            "mygpo": ClientConfigService(baseurl=baseurl).model_dump(),
            "mygpo-feedservice": ClientConfigService(baseurl=baseurl).model_dump(),
            "update_timeout": DEFAULT_UPDATE_TIMEOUT_SECONDS,
        }
    )
