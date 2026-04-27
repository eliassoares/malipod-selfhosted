from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import func, select

from app.core.placeholders import choose_placeholder_url_stable
from app.core.time_format import format_duration_short
from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    EpisodeActionEventModel,
    EpisodeModel,
    PodcastFeedModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel

SortMode = Literal["recent", "oldest"]

_COMPLETED_THRESHOLD = 0.90
_COMPLETED_REMAINING_SECS = 120


def is_episode_completed(play_position: int | None, play_total: int | None) -> bool:
    if play_position is None or play_total is None:
        return False
    if play_total <= 0:
        return False
    remaining = play_total - play_position
    return (
        remaining <= _COMPLETED_REMAINING_SECS
        or play_position / play_total >= _COMPLETED_THRESHOLD
    )


@dataclass(slots=True)
class EpisodeCard:
    id: int
    title: str
    released_at: datetime
    logo_url: str
    description: str | None
    archive_status: str = field(default="none")
    archive_path: str | None = field(default=None)
    archive_error: str | None = field(default=None)
    play_position: int | None = field(default=None)
    play_total: int | None = field(default=None)

    @property
    def is_completed(self) -> bool:
        return is_episode_completed(self.play_position, self.play_total)

    @property
    def progress_pct(self) -> int:
        if self.play_position is None or not self.play_total:
            return 0
        return min(100, int(self.play_position / self.play_total * 100))


@dataclass(slots=True)
class PodcastListeningStats:
    episodes_played: int
    total_seconds: int

    def format_total_time(self) -> str:
        return format_duration_short(self.total_seconds)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class PodcastDetailService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_feed(self, *, feed_id: int) -> PodcastFeedModel | None:
        result = await self.session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.id == feed_id)
        )
        return result.scalar_one_or_none()

    async def _build_play_index(
        self, user_id: int, feed_id: int
    ) -> dict[int, tuple[int, int]]:
        """Returns {episode_id: (max_position, max_total)} for played episodes."""
        play_subq = (
            select(
                EpisodeActionEventModel.episode_id,
                func.max(EpisodeActionEventModel.position).label("max_pos"),
                func.max(EpisodeActionEventModel.total).label("max_total"),
            )
            .join(EpisodeModel, EpisodeModel.id == EpisodeActionEventModel.episode_id)
            .where(
                EpisodeActionEventModel.user_id == user_id,
                EpisodeModel.feed_id == feed_id,
                EpisodeActionEventModel.action == "play",
                EpisodeActionEventModel.position.is_not(None),
            )
            .group_by(EpisodeActionEventModel.episode_id)
        )
        rows = (await self.session.execute(play_subq)).all()
        return {row.episode_id: (row.max_pos or 0, row.max_total or 0) for row in rows}

    async def get_listening_stats(
        self, user: UserModel, *, feed_id: int
    ) -> PodcastListeningStats:
        play_index = await self._build_play_index(user.id, feed_id)
        total_seconds = sum(pos for pos, _ in play_index.values())
        return PodcastListeningStats(
            episodes_played=len(play_index),
            total_seconds=total_seconds,
        )

    async def list_episodes(
        self,
        *,
        feed_id: int,
        sort: SortMode,
        fallback_logo_url: str | None = None,
        user: UserModel | None = None,
    ) -> list[EpisodeCard]:
        statement = select(EpisodeModel).where(EpisodeModel.feed_id == feed_id)
        if sort == "oldest":
            statement = statement.order_by(
                EpisodeModel.released_at.asc(),
                EpisodeModel.id.asc(),
            )
        else:
            statement = statement.order_by(
                EpisodeModel.released_at.desc(),
                EpisodeModel.id.desc(),
            )

        episodes = (await self.session.execute(statement)).scalars().all()

        play_index: dict[int, tuple[int, int]] = {}
        if user is not None:
            play_index = await self._build_play_index(user.id, feed_id)

        cards: list[EpisodeCard] = []
        for episode in episodes:
            raw = (episode.logo_url or "").strip()
            if raw and not raw.startswith("/static/"):
                logo_url = raw
            else:
                logo_url = fallback_logo_url or choose_placeholder_url_stable(
                    episode.episode_url
                )
            play_entry = play_index.get(episode.id)
            play_pos = play_entry[0] if play_entry else None
            play_total = play_entry[1] if play_entry else None
            cards.append(
                EpisodeCard(
                    id=episode.id,
                    title=episode.title,
                    released_at=_normalize_timestamp(episode.released_at),
                    logo_url=logo_url,
                    description=episode.description,
                    archive_status=episode.archive_status,
                    archive_path=episode.archive_path,
                    archive_error=episode.archive_error,
                    play_position=play_pos,
                    play_total=play_total,
                )
            )
        return cards

    async def is_user_subscribed(
        self,
        user: UserModel,
        *,
        feed_id: int,
    ) -> bool:
        result = await self.session.execute(
            select(DeviceSubscriptionModel.id)
            .join(DeviceModel, DeviceModel.id == DeviceSubscriptionModel.device_pk)
            .where(
                DeviceModel.user_id == user.id,
                DeviceSubscriptionModel.feed_id == feed_id,
                DeviceSubscriptionModel.unsubscribed_at.is_(None),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_last_played_at(
        self,
        user: UserModel,
        *,
        feed_id: int,
    ) -> datetime | None:
        statement = (
            select(EpisodeActionEventModel.occurred_at)
            .join(EpisodeModel, EpisodeModel.id == EpisodeActionEventModel.episode_id)
            .where(
                EpisodeActionEventModel.user_id == user.id,
                EpisodeModel.feed_id == feed_id,
                EpisodeActionEventModel.action == "play",
            )
            .order_by(
                EpisodeActionEventModel.occurred_at.desc(),
                EpisodeActionEventModel.id.desc(),
            )
            .limit(1)
        )
        row = (await self.session.execute(statement)).scalar_one_or_none()
        if row is None:
            return None
        return _normalize_timestamp(row)


@dataclass(slots=True)
class PodcastCompletionMetrics:
    completed_episodes: int
    total_episodes: int
    in_progress_episodes: int
    completion_rate_pct: int | None


def compute_podcast_completion_metrics(
    episodes: list[EpisodeCard],
) -> PodcastCompletionMetrics:
    total = len(episodes)
    completed = sum(1 for episode in episodes if episode.is_completed)
    in_progress = sum(
        1
        for episode in episodes
        if (episode.play_position or 0) > 0 and not episode.is_completed
    )
    completion_rate_pct = None
    if total > 0:
        completion_rate_pct = min(100, round(completed / total * 100))
    return PodcastCompletionMetrics(
        completed_episodes=completed,
        total_episodes=total,
        in_progress_episodes=in_progress,
        completion_rate_pct=completion_rate_pct,
    )
