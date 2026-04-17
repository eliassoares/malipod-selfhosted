from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.auth_api import router as auth_api_router
from app.api.routes.auth_site import router as auth_site_router
from app.api.routes.devices_api import router as devices_api_router
from app.api.routes.episodes_api import router as episodes_api_router
from app.api.routes.favorites_api import router as favorites_api_router
from app.api.routes.health import router as health_router
from app.api.routes.lists_api import router as lists_api_router
from app.api.routes.profile_site import router as profile_site_router
from app.api.routes.settings_api import router as settings_api_router
from app.api.routes.site import router as site_router
from app.api.routes.subscriptions_api import router as subscriptions_api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import close_database_connections, initialize_database

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    await initialize_database(settings)
    try:
        yield
    finally:
        await close_database_connections()


def create_app() -> FastAPI:
    app = FastAPI(title="Malipod", version="0.1.0", lifespan=lifespan)
    app.include_router(site_router)
    app.include_router(auth_site_router)
    app.include_router(profile_site_router)
    app.include_router(health_router)
    app.include_router(auth_api_router)
    app.include_router(devices_api_router)
    app.include_router(episodes_api_router)
    app.include_router(favorites_api_router)
    app.include_router(lists_api_router)
    app.include_router(settings_api_router)
    app.include_router(subscriptions_api_router)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    return app


app = create_app()
