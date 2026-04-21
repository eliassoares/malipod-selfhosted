from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Response

    from app.core.config import Settings


def apply_locale_cookie(response: Response, settings: Settings, locale: str) -> None:
    response.set_cookie(
        key="malipod_locale",
        value=locale,
        httponly=False,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=settings.session_ttl_seconds,
    )
