from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import Select, select
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


class SettingsError(Exception):
    def __init__(self, code: Literal["target_not_found"]) -> None:
        self.code = code
        super().__init__(code)


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _fetch_scalar[T](self, statement: Select[tuple[T]]) -> T | None:
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    def _copy_settings(document: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(document, dict):
            return {}
        return dict(document)

    async def _get_device(self, user: UserModel, device_id: str) -> DeviceModel:
        device = await self._fetch_scalar(
            select(DeviceModel).where(
                DeviceModel.user_id == user.id,
                DeviceModel.device_id == device_id,
            )
        )
        if device is None:
            raise SettingsError("target_not_found")
        return device

    async def _get_feed(self, podcast_url: str) -> PodcastFeedModel:
        feed = await self._fetch_scalar(
            select(PodcastFeedModel).where(PodcastFeedModel.feed_url == podcast_url)
        )
        if feed is None:
            raise SettingsError("target_not_found")
        return feed

    async def _get_episode(self, podcast_url: str, episode_url: str) -> EpisodeModel:
        episode = await self._fetch_scalar(
            select(EpisodeModel)
            .options(selectinload(EpisodeModel.feed))
            .join(EpisodeModel.feed)
            .where(
                EpisodeModel.episode_url == episode_url,
                PodcastFeedModel.feed_url == podcast_url,
            )
        )
        if episode is None:
            raise SettingsError("target_not_found")
        return episode

    async def get_settings(
        self, user: UserModel, query: SettingsScopeQuery
    ) -> SettingsDocument:
        if query.scope == "account":
            return await self._get_account_settings(user)
        if query.scope == "device":
            return await self._get_device_settings(user, query.device or "")
        if query.scope == "podcast":
            return await self._get_podcast_settings(user, query.podcast or "")
        return await self._get_episode_settings(
            user,
            query.podcast or "",
            query.episode or "",
        )

    async def save_settings(
        self,
        user: UserModel,
        query: SettingsScopeQuery,
        payload: SettingsMutationRequest,
    ) -> SettingsDocument:
        if query.scope == "account":
            return await self._save_account_settings(user, payload)
        if query.scope == "device":
            return await self._save_device_settings(user, query.device or "", payload)
        if query.scope == "podcast":
            return await self._save_podcast_settings(user, query.podcast or "", payload)
        return await self._save_episode_settings(
            user,
            query.podcast or "",
            query.episode or "",
            payload,
        )

    def _apply_mutation(
        self,
        current: dict[str, Any],
        payload: SettingsMutationRequest,
    ) -> dict[str, Any]:
        updated = dict(current)
        for key in payload.remove:
            updated.pop(key, None)
        for key, value in payload.set.items():
            updated[key] = value
        return updated

    async def _get_account_settings(self, user: UserModel) -> SettingsDocument:
        document = await self._fetch_scalar(
            select(AccountSettingModel).where(AccountSettingModel.user_id == user.id)
        )
        return SettingsDocument.from_mapping(
            self._copy_settings(document.settings if document else None)
        )

    async def _save_account_settings(
        self,
        user: UserModel,
        payload: SettingsMutationRequest,
    ) -> SettingsDocument:
        document = await self._fetch_scalar(
            select(AccountSettingModel).where(AccountSettingModel.user_id == user.id)
        )
        now = datetime.now(UTC)
        current = self._copy_settings(document.settings if document else None)
        updated = self._apply_mutation(current, payload)
        if document is None:
            document = AccountSettingModel(
                user_id=user.id,
                settings=updated,
                created_at=now,
                updated_at=now,
            )
            self.session.add(document)
        else:
            document.settings = updated
            document.updated_at = now
        await self.session.commit()
        return SettingsDocument.from_mapping(updated)

    async def _get_device_settings(
        self, user: UserModel, device_id: str
    ) -> SettingsDocument:
        device = await self._get_device(user, device_id)
        document = await self._fetch_scalar(
            select(DeviceSettingModel).where(
                DeviceSettingModel.user_id == user.id,
                DeviceSettingModel.device_pk == device.id,
            )
        )
        return SettingsDocument.from_mapping(
            self._copy_settings(document.settings if document else None)
        )

    async def _save_device_settings(
        self,
        user: UserModel,
        device_id: str,
        payload: SettingsMutationRequest,
    ) -> SettingsDocument:
        device = await self._get_device(user, device_id)
        document = await self._fetch_scalar(
            select(DeviceSettingModel).where(
                DeviceSettingModel.user_id == user.id,
                DeviceSettingModel.device_pk == device.id,
            )
        )
        now = datetime.now(UTC)
        current = self._copy_settings(document.settings if document else None)
        updated = self._apply_mutation(current, payload)
        if document is None:
            document = DeviceSettingModel(
                user_id=user.id,
                device_pk=device.id,
                settings=updated,
                created_at=now,
                updated_at=now,
            )
            self.session.add(document)
        else:
            document.settings = updated
            document.updated_at = now
        await self.session.commit()
        return SettingsDocument.from_mapping(updated)

    async def _get_podcast_settings(
        self, user: UserModel, podcast_url: str
    ) -> SettingsDocument:
        feed = await self._get_feed(podcast_url)
        document = await self._fetch_scalar(
            select(PodcastSettingModel).where(
                PodcastSettingModel.user_id == user.id,
                PodcastSettingModel.feed_id == feed.id,
            )
        )
        return SettingsDocument.from_mapping(
            self._copy_settings(document.settings if document else None)
        )

    async def _save_podcast_settings(
        self,
        user: UserModel,
        podcast_url: str,
        payload: SettingsMutationRequest,
    ) -> SettingsDocument:
        feed = await self._get_feed(podcast_url)
        document = await self._fetch_scalar(
            select(PodcastSettingModel).where(
                PodcastSettingModel.user_id == user.id,
                PodcastSettingModel.feed_id == feed.id,
            )
        )
        now = datetime.now(UTC)
        current = self._copy_settings(document.settings if document else None)
        updated = self._apply_mutation(current, payload)
        if document is None:
            document = PodcastSettingModel(
                user_id=user.id,
                feed_id=feed.id,
                settings=updated,
                created_at=now,
                updated_at=now,
            )
            self.session.add(document)
        else:
            document.settings = updated
            document.updated_at = now
        await self.session.commit()
        return SettingsDocument.from_mapping(updated)

    async def _get_episode_settings(
        self, user: UserModel, podcast_url: str, episode_url: str
    ) -> SettingsDocument:
        episode = await self._get_episode(podcast_url, episode_url)
        document = await self._fetch_scalar(
            select(EpisodeSettingModel).where(
                EpisodeSettingModel.user_id == user.id,
                EpisodeSettingModel.episode_id == episode.id,
            )
        )
        return SettingsDocument.from_mapping(
            self._copy_settings(document.settings if document else None)
        )

    async def _save_episode_settings(
        self,
        user: UserModel,
        podcast_url: str,
        episode_url: str,
        payload: SettingsMutationRequest,
    ) -> SettingsDocument:
        episode = await self._get_episode(podcast_url, episode_url)
        document = await self._fetch_scalar(
            select(EpisodeSettingModel).where(
                EpisodeSettingModel.user_id == user.id,
                EpisodeSettingModel.episode_id == episode.id,
            )
        )
        now = datetime.now(UTC)
        current = self._copy_settings(document.settings if document else None)
        updated = self._apply_mutation(current, payload)
        if document is None:
            document = EpisodeSettingModel(
                user_id=user.id,
                episode_id=episode.id,
                settings=updated,
                created_at=now,
                updated_at=now,
            )
            self.session.add(document)
        else:
            document.settings = updated
            document.updated_at = now
        await self.session.commit()
        return SettingsDocument.from_mapping(updated)
