from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from app.services.localization import LocalizationService

if TYPE_CHECKING:
    from app.core.config import Settings
    from app.db.models.user import UserModel


def test_localization_prefers_authenticated_user_locale(settings: Settings) -> None:
    service = LocalizationService(settings)
    user = cast("UserModel", SimpleNamespace(language_preference="pt-BR"))

    resolved = service.resolve_locale("es", user=user)

    assert resolved.effective_locale == "pt-BR"
    assert resolved.source == "user"


def test_localization_uses_cookie_for_guest(settings: Settings) -> None:
    service = LocalizationService(settings)

    resolved = service.resolve_locale("es")

    assert resolved.effective_locale == "es"
    assert resolved.source == "cookie_or_form"


def test_localization_falls_back_to_default_for_invalid_locale(
    settings: Settings,
) -> None:
    service = LocalizationService(settings)

    resolved = service.resolve_locale("de")

    assert resolved.effective_locale == settings.default_locale
    assert resolved.source == "default"
