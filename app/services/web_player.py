from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.placeholders import resolve_image_url
from app.db.models.device import DeviceModel
from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.schemas.episode import EpisodeActionInput
from app.services.episodes import EpisodeService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings
    from app.db.models.user import UserModel
    from app.schemas.web_player import PlayerActionInput, PlayerStateInput


class WebPlayerError(Exception):
    def __init__(
        self,
        code: Literal["episode_not_found"],
    ) -> None:
        self.code = code
        super().__init__(code)


WEB_PLAYER_DEVICE_ID = "web-player"
WEB_PLAYER_DEVICE_TYPE = "browser"
WEB_PLAYER_DEVICE_CAPTION = "MaliPod Web Player"


class WebPlayerService:
    def __init__(self, *, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.episode_service = EpisodeService(session)

    async def get_or_create_web_device(self, user: UserModel) -> DeviceModel:
        now = datetime.now(UTC)
        stmt = (
            insert(DeviceModel)
            .values(
                user_id=user.id,
                device_id=WEB_PLAYER_DEVICE_ID,
                caption=WEB_PLAYER_DEVICE_CAPTION,
                device_type=WEB_PLAYER_DEVICE_TYPE,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_nothing(constraint="uq_devices_user_id_device_id")
        )
        await self.session.execute(stmt)
        await self.session.commit()

        device = (
            await self.session.execute(
                select(DeviceModel).where(
                    DeviceModel.user_id == user.id,
                    DeviceModel.device_id == WEB_PLAYER_DEVICE_ID,
                )
            )
        ).scalar_one()
        return device

    async def upsert_state(self, user: UserModel, payload: PlayerStateInput) -> None:
        if payload.episode_id is None:
            user.last_episode_id = None
            user.last_position_sec = None
            user.last_queue_mode = None
            user.last_queue_ref_id = None
            await self.session.commit()
            return

        episode = (
            await self.session.execute(
                select(EpisodeModel).where(EpisodeModel.id == payload.episode_id)
            )
        ).scalar_one_or_none()
        if episode is None:
            raise WebPlayerError("episode_not_found")

        user.last_episode_id = payload.episode_id
        user.last_position_sec = payload.position_sec
        user.last_queue_mode = payload.queue_mode
        user.last_queue_ref_id = payload.queue_ref_id
        user.updated_at = datetime.now(UTC)
        await self.session.commit()

    async def record_action(self, user: UserModel, payload: PlayerActionInput) -> None:
        episode_row = (
            await self.session.execute(
                select(EpisodeModel, PodcastFeedModel.feed_url)
                .join(PodcastFeedModel, PodcastFeedModel.id == EpisodeModel.feed_id)
                .where(EpisodeModel.id == payload.episode_id)
            )
        ).one_or_none()
        if episode_row is None:
            raise WebPlayerError("episode_not_found")
        episode, podcast_url = episode_row
        await self.get_or_create_web_device(user)

        occurred_at = payload.timestamp or datetime.now(UTC)
        # gpodder uses "play" with started/position for progress; "pause"/"stop"
        # are non-standard and ignored by clients like AntennaPod.
        gpodder_action = (
            "play" if payload.action in {"pause", "stop"} else payload.action
        )
        # AntennaPod identifies episodes by enclosure URL (media_url), not the
        # RSS <link>/guid. Fall back to episode_url only if media_url is absent.
        episode_identifier = episode.media_url or episode.episode_url
        action = EpisodeActionInput(
            podcast=podcast_url,
            episode=episode_identifier,
            device=WEB_PLAYER_DEVICE_ID,
            action=gpodder_action,
            timestamp=occurred_at,
            started=payload.started,
            position=payload.position,
            total=payload.total,
        )
        await self.episode_service.upload_actions(user, [action])

    async def get_next_episode_id(self, *, episode_id: int) -> int | None:
        current = (
            await self.session.execute(
                select(EpisodeModel).where(EpisodeModel.id == episode_id)
            )
        ).scalar_one_or_none()
        if current is None:
            raise WebPlayerError("episode_not_found")

        statement = (
            select(EpisodeModel.id)
            .where(
                EpisodeModel.feed_id == current.feed_id,
                (EpisodeModel.released_at < current.released_at)
                | (
                    (EpisodeModel.released_at == current.released_at)
                    & (EpisodeModel.id < current.id)
                ),
            )
            .order_by(EpisodeModel.released_at.desc(), EpisodeModel.id.desc())
            .limit(1)
        )
        next_id = (await self.session.execute(statement)).scalar_one_or_none()
        if next_id is None:
            return None
        return int(next_id)

    async def get_episode_info(self, *, episode_id: int) -> dict[str, object]:
        row = (
            await self.session.execute(
                select(EpisodeModel, PodcastFeedModel.title)
                .join(PodcastFeedModel, PodcastFeedModel.id == EpisodeModel.feed_id)
                .where(EpisodeModel.id == episode_id)
            )
        ).one_or_none()
        if row is None:
            raise WebPlayerError("episode_not_found")
        episode, podcast_title = row
        return {
            "episode_id": episode.id,
            "feed_id": episode.feed_id,
            "media_url": episode.media_url,
            "episode_title": episode.title,
            "podcast_title": podcast_title,
            "cover_url": resolve_image_url(episode.logo_url, seed=episode.episode_url),
        }
