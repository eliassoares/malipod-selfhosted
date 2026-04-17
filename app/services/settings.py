from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.device import DeviceModel
from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.db.models.settings import (
    AccountSettingModel,
    DeviceSettingModel,
    EpisodeSettingModel,
    PodcastSettingModel,
)
from app.schemas.setting import (
    SettingsDocument,
    SettingsMutationRequest,
    SettingsScopeQuery,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel

type SettingModel = (
    AccountSettingModel | DeviceSettingModel | PodcastSettingModel | EpisodeSettingModel
)


class SettingsError(Exception):
    def __init__(self, code: Literal["target_not_found"]) -> None:
        self.code = code
        super().__init__(code)


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_device(self, user: UserModel, device_id: str) -> DeviceModel:
        result = await self.session.execute(
            select(DeviceModel).where(
                DeviceModel.user_id == user.id,
                DeviceModel.device_id == device_id,
            )
        )
        device = result.scalar_one_or_none()
        if device is None:
            raise SettingsError("target_not_found")
        return device

    async def _get_feed(self, podcast_url: str) -> PodcastFeedModel:
        result = await self.session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.feed_url == podcast_url)
        )
        feed = result.scalar_one_or_none()
        if feed is None:
            raise SettingsError("target_not_found")
        return feed

    async def _get_episode(self, podcast_url: str, episode_url: str) -> EpisodeModel:
        result = await self.session.execute(
            select(EpisodeModel)
            .options(selectinload(EpisodeModel.feed))
            .join(EpisodeModel.feed)
            .where(
                EpisodeModel.episode_url == episode_url,
                PodcastFeedModel.feed_url == podcast_url,
            )
        )
        episode = result.scalar_one_or_none()
        if episode is None:
            raise SettingsError("target_not_found")
        return episode

    async def _resolve_scope(
        self, user: UserModel, query: SettingsScopeQuery
    ) -> tuple[type[SettingModel], dict[str, Any]]:
        if query.scope == "account":
            return AccountSettingModel, {"user_id": user.id}
        if query.scope == "device":
            device = await self._get_device(user, query.device or "")
            return DeviceSettingModel, {"user_id": user.id, "device_pk": device.id}
        if query.scope == "podcast":
            feed = await self._get_feed(query.podcast or "")
            return PodcastSettingModel, {"user_id": user.id, "feed_id": feed.id}
        episode = await self._get_episode(query.podcast or "", query.episode or "")
        return EpisodeSettingModel, {"user_id": user.id, "episode_id": episode.id}

    async def _fetch_row(
        self, model_cls: type[SettingModel], filters: dict[str, Any]
    ) -> SettingModel | None:
        conditions = [
            getattr(model_cls, key) == value for key, value in filters.items()
        ]
        result = await self.session.execute(select(model_cls).where(*conditions))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return row  # type: ignore[return-value]

    @staticmethod
    def _read_settings(row: SettingModel | None) -> dict[str, Any]:
        if row is None or not isinstance(row.settings, dict):
            return {}
        return dict(row.settings)

    @staticmethod
    def _apply_mutation(
        current: dict[str, Any], payload: SettingsMutationRequest
    ) -> dict[str, Any]:
        updated = dict(current)
        for key, value in payload.set.items():
            updated[key] = value
        for key in payload.remove:
            updated.pop(key, None)
        return updated

    async def get_settings(
        self, user: UserModel, query: SettingsScopeQuery
    ) -> SettingsDocument:
        model_cls, filters = await self._resolve_scope(user, query)
        row = await self._fetch_row(model_cls, filters)
        return SettingsDocument.from_mapping(self._read_settings(row))

    async def save_settings(
        self,
        user: UserModel,
        query: SettingsScopeQuery,
        payload: SettingsMutationRequest,
    ) -> SettingsDocument:
        model_cls, filters = await self._resolve_scope(user, query)
        row = await self._fetch_row(model_cls, filters)
        current = self._read_settings(row)
        updated = self._apply_mutation(current, payload)
        now = datetime.now(UTC)
        if row is None:
            row = model_cls(**filters, settings=updated, created_at=now, updated_at=now)
            self.session.add(row)
        else:
            row.settings = updated
            row.updated_at = now
        await self.session.commit()
        return SettingsDocument.from_mapping(updated)
