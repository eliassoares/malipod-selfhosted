"""Route modules for the application."""

from app.api.routes.episodes_api import router as episodes_api_router
from app.api.routes.favorites_api import router as favorites_api_router
from app.api.routes.lists_api import router as lists_api_router
from app.api.routes.settings_api import router as settings_api_router

__all__ = [
    "episodes_api_router",
    "favorites_api_router",
    "lists_api_router",
    "settings_api_router",
]
