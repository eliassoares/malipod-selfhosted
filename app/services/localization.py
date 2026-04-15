from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.localization import (
    DEFAULT_LOCALE_CODE,
    LocaleResolution,
    get_translation_catalog,
    is_supported_locale,
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
        requested_locale = normalize_locale(explicit_locale) or normalize_locale(
            cookie_locale
        )
        if user is not None:
            effective_locale = normalize_locale(user.language_preference) or (
                self.settings.default_locale
            )
            return LocaleResolution(
                requested_locale=requested_locale,
                effective_locale=effective_locale,
                source="user",
                is_supported=is_supported_locale(requested_locale),
            )
        if requested_locale is not None:
            return LocaleResolution(
                requested_locale=requested_locale,
                effective_locale=requested_locale,
                source="cookie_or_form",
                is_supported=True,
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
