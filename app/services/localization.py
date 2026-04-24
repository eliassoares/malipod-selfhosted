from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.localization import (
    DEFAULT_LOCALE_CODE,
    LocaleResolution,
    get_translation_catalog,
    normalize_locale,
)

if TYPE_CHECKING:
    from app.core.config import Settings
    from app.db.models.user import UserModel


class LocalizationService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def resolve_locale(
        self,
        cookie_locale: str | None,
        user: UserModel | None = None,
        explicit_locale: str | None = None,
    ) -> LocaleResolution:
        normalized_explicit = normalize_locale(explicit_locale)
        normalized_cookie = normalize_locale(cookie_locale)
        if normalized_explicit is not None:
            return LocaleResolution(
                requested_locale=normalized_explicit,
                effective_locale=normalized_explicit,
                source="explicit",
                is_supported=True,
            )
        if normalized_cookie is not None:
            return LocaleResolution(
                requested_locale=normalized_cookie,
                effective_locale=normalized_cookie,
                source="cookie_or_form",
                is_supported=True,
            )
        if user is not None:
            effective_locale = normalize_locale(user.language_preference) or (
                self.settings.default_locale
            )
            return LocaleResolution(
                requested_locale=None,
                effective_locale=effective_locale,
                source="user",
                is_supported=False,
            )
        return LocaleResolution(
            requested_locale=None,
            effective_locale=self.settings.default_locale,
            source="default",
            is_supported=False,
        )

    def build_copy(self, locale: str) -> dict[str, str]:
        normalized = normalize_locale(locale) or DEFAULT_LOCALE_CODE
        return get_translation_catalog(normalized)
