from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.core.security import sanitize_episode_url
from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    EpisodeActionEventModel,
    EpisodeActionModel,
    EpisodeModel,
    PodcastFeedModel,
)
from app.schemas.episode import (
    EpisodeActionInput,
    EpisodeActionOutput,
    EpisodeActionQuery,
    EpisodeActionQueryResponse,
    EpisodeActionUploadResponse,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel


@dataclass(slots=True)
class NormalizedUrlChange:
    original: str
    sanitized: str


class EpisodeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _fetch_device_statement(
        self,
        statement: Select[tuple[DeviceModel]],
    ) -> DeviceModel | None:
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def _resolve_device(
        self,
        user: UserModel,
        device_id: str | None,
    ) -> DeviceModel | None:
        if device_id is None:
            return None
        return await self._fetch_device_statement(
            select(DeviceModel).where(
                DeviceModel.user_id == user.id,
                DeviceModel.device_id == device_id,
            )
        )

    async def _get_or_create_feed(self, url: str) -> PodcastFeedModel:
        result = await self.session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.feed_url == url)
        )
        feed = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if feed is None:
            feed = PodcastFeedModel(
                feed_url=url,
                title=url,
                description=None,
                website=None,
                logo_url=None,
                mygpo_link=None,
                created_at=now,
                updated_at=now,
            )
            self.session.add(feed)
            await self.session.flush()
            return feed
        return feed

    async def _get_or_create_episode(
        self,
        *,
        feed: PodcastFeedModel,
        episode_url: str,
        occurred_at: datetime,
    ) -> EpisodeModel:
        result = await self.session.execute(
            select(EpisodeModel).where(EpisodeModel.episode_url == episode_url)
        )
        episode = result.scalar_one_or_none()
        if episode is None:
            result = await self.session.execute(
                select(EpisodeModel).where(
                    EpisodeModel.feed_id == feed.id,
                    EpisodeModel.media_url == episode_url,
                )
            )
            episode = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if episode is None:
            episode = EpisodeModel(
                feed_id=feed.id,
                episode_url=episode_url,
                title="Untitled episode",
                description=None,
                website=None,
                mygpo_link=None,
                released_at=occurred_at,
                created_at=now,
                updated_at=now,
            )
            self.session.add(episode)
            await self.session.flush()
            return episode
        if episode.feed_id != feed.id:
            episode.feed_id = feed.id
        episode.updated_at = now
        await self.session.flush()
        return episode

    async def _get_or_create_projection(
        self,
        *,
        user_id: int,
        episode_id: int,
    ) -> EpisodeActionModel | None:
        result = await self.session.execute(
            select(EpisodeActionModel).where(
                EpisodeActionModel.user_id == user_id,
                EpisodeActionModel.episode_id == episode_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _build_projection_action(
        action: str,
        *,
        started: int | None,
        position: int | None,
        total: int | None,
    ) -> dict[str, Any] | None:
        if action == "new":
            return None
        if action in {"play", "pause"}:
            return {
                "started": started,
                "position": position,
                "total": total,
            }
        return {}

    async def _upsert_projection(
        self,
        *,
        user: UserModel,
        episode: EpisodeModel,
        device: DeviceModel | None,
        action: str,
        occurred_at: datetime,
        started: int | None,
        position: int | None,
        total: int | None,
    ) -> None:
        projection = await self._get_or_create_projection(
            user_id=user.id,
            episode_id=episode.id,
        )
        now = datetime.now(UTC)
        payload = self._build_projection_action(
            action,
            started=started,
            position=position,
            total=total,
        )
        if projection is None:
            projection = EpisodeActionModel(
                user_id=user.id,
                device_pk=device.id if device is not None else None,
                episode_id=episode.id,
                status=action,
                action=payload,
                occurred_at=occurred_at,
                updated_at=now,
            )
            self.session.add(projection)
            await self.session.flush()
            return

        projection.device_pk = device.id if device is not None else None
        projection.status = action
        projection.action = payload
        projection.occurred_at = occurred_at
        projection.updated_at = now
        await self.session.flush()

    @staticmethod
    def _normalize_timestamp(value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(UTC)
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @staticmethod
    def _track_url_change(
        changes: OrderedDict[tuple[str, str], None],
        *,
        original: str,
        sanitized: str,
    ) -> None:
        if original != sanitized:
            changes[(original, sanitized)] = None

    async def _current_timestamp(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.max(EpisodeActionEventModel.id)).where(
                EpisodeActionEventModel.user_id == user_id
            )
        )
        timestamp = result.scalar_one()
        return int(timestamp or 0)

    async def upload_actions(
        self,
        user: UserModel,
        actions: Sequence[EpisodeActionInput],
    ) -> EpisodeActionUploadResponse:
        rewritten: OrderedDict[tuple[str, str], None] = OrderedDict()
        for item in actions:
            sanitized_podcast = sanitize_episode_url(item.podcast)
            sanitized_episode = sanitize_episode_url(item.episode)
            self._track_url_change(
                rewritten,
                original=item.podcast,
                sanitized=sanitized_podcast,
            )
            self._track_url_change(
                rewritten,
                original=item.episode,
                sanitized=sanitized_episode,
            )
            if not sanitized_podcast or not sanitized_episode:
                continue

            occurred_at = self._normalize_timestamp(item.timestamp)
            device = await self._resolve_device(user, item.device)
            feed = await self._get_or_create_feed(sanitized_podcast)
            episode = await self._get_or_create_episode(
                feed=feed,
                episode_url=sanitized_episode,
                occurred_at=occurred_at,
            )
            event = EpisodeActionEventModel(
                user_id=user.id,
                episode_id=episode.id,
                podcast_url=sanitized_podcast,
                episode_url=sanitized_episode,
                device_id=item.device,
                action=item.action,
                occurred_at=occurred_at,
                started=item.started,
                position=item.position,
                total=item.total,
                created_at=datetime.now(UTC),
            )
            self.session.add(event)
            await self.session.flush()
            await self._upsert_projection(
                user=user,
                episode=episode,
                device=device,
                action=item.action,
                occurred_at=occurred_at,
                started=item.started,
                position=item.position,
                total=item.total,
            )
            if (
                item.action == "play"
                and item.position is not None
                and episode.id == user.last_episode_id
            ):
                user.last_position_sec = item.position

        await self.session.commit()
        return EpisodeActionUploadResponse(
            timestamp=await self._current_timestamp(user.id),
            update_urls=list(rewritten),
        )

    @staticmethod
    def _serialize_action(model: EpisodeActionEventModel) -> EpisodeActionOutput:
        return EpisodeActionOutput(
            podcast=model.podcast_url,
            episode=model.episode_url,
            device=model.device_id,
            action=model.action,
            timestamp=model.occurred_at,
            started=model.started,
            position=model.position,
            total=model.total,
        )

    async def list_actions(
        self,
        user: UserModel,
        query: EpisodeActionQuery,
    ) -> EpisodeActionQueryResponse:
        statement = (
            select(EpisodeActionEventModel)
            .options(
                selectinload(EpisodeActionEventModel.episode).selectinload(
                    EpisodeModel.feed
                )
            )
            .where(EpisodeActionEventModel.user_id == user.id)
            .order_by(EpisodeActionEventModel.id.asc())
        )
        if query.since is not None:
            statement = statement.where(EpisodeActionEventModel.id > query.since)
        if query.podcast is not None:
            statement = statement.where(
                EpisodeActionEventModel.podcast_url == query.podcast
            )
        if query.device is not None:
            statement = statement.where(
                EpisodeActionEventModel.device_id == query.device
            )

        result = await self.session.execute(statement)
        models = list(result.scalars().all())
        if query.aggregated:
            latest_by_episode: dict[int, EpisodeActionEventModel] = {}
            for model in models:
                latest_by_episode[model.episode_id] = model
            models = sorted(latest_by_episode.values(), key=lambda item: item.id)

        return EpisodeActionQueryResponse(
            actions=[self._serialize_action(model) for model in models],
            timestamp=await self._current_timestamp(user.id),
        )
