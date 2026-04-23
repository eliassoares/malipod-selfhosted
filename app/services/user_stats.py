from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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
from app.services.podcast_detail import is_episode_completed

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql.selectable import Subquery

    from app.db.models.user import UserModel


@dataclass(slots=True)
class UserStatsHighlights:
    listened_seconds: int
    completed_episodes: int
    followed_podcasts: int

    @property
    def listened_formatted(self) -> str:
        return format_duration_short(self.listened_seconds)


@dataclass(slots=True)
class PodcastTimeRank:
    feed_id: int
    title: str
    logo_url: str
    listened_seconds: int

    @property
    def listened_formatted(self) -> str:
        return format_duration_short(self.listened_seconds)


@dataclass(slots=True)
class PodcastCompletedRank:
    feed_id: int
    title: str
    logo_url: str
    completed_episodes: int
    total_episodes: int


@dataclass(slots=True)
class UserStatsPayload:
    highlights: UserStatsHighlights
    top_by_time: list[PodcastTimeRank]
    top_by_completed: list[PodcastCompletedRank]


class UserStatsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _count_followed_podcasts(self, user_id: int) -> int:
        statement = (
            select(func.count(func.distinct(DeviceSubscriptionModel.feed_id)))
            .join(DeviceModel, DeviceModel.id == DeviceSubscriptionModel.device_pk)
            .where(
                DeviceModel.user_id == user_id,
                DeviceSubscriptionModel.unsubscribed_at.is_(None),
            )
        )
        value = (await self.session.execute(statement)).scalar_one()
        return int(value or 0)

    def _episode_play_index(self, user_id: int) -> Subquery:
        return (
            select(
                EpisodeActionEventModel.episode_id.label("episode_id"),
                EpisodeModel.feed_id.label("feed_id"),
                func.max(EpisodeActionEventModel.position).label("max_pos"),
                func.max(EpisodeActionEventModel.total).label("max_total"),
            )
            .join(EpisodeModel, EpisodeModel.id == EpisodeActionEventModel.episode_id)
            .where(
                EpisodeActionEventModel.user_id == user_id,
                EpisodeActionEventModel.action == "play",
                EpisodeActionEventModel.position.is_not(None),
            )
            .group_by(EpisodeActionEventModel.episode_id, EpisodeModel.feed_id)
            .subquery()
        )

    async def build(self, user: UserModel) -> UserStatsPayload:
        followed_podcasts = await self._count_followed_podcasts(user.id)

        play_index = self._episode_play_index(user.id)
        play_rows = (await self.session.execute(select(play_index))).all()

        listened_seconds = sum(int(row.max_pos or 0) for row in play_rows)
        completed_episodes = sum(
            1 for row in play_rows if is_episode_completed(row.max_pos, row.max_total)
        )

        top_by_time: list[PodcastTimeRank] = []
        top_time_statement = (
            select(
                PodcastFeedModel.id,
                PodcastFeedModel.title,
                PodcastFeedModel.feed_url,
                PodcastFeedModel.logo_url,
                func.sum(play_index.c.max_pos).label("sum_pos"),
            )
            .join(play_index, play_index.c.feed_id == PodcastFeedModel.id)
            .group_by(PodcastFeedModel.id)
            .order_by(func.sum(play_index.c.max_pos).desc(), PodcastFeedModel.id.asc())
            .limit(5)
        )
        for feed_id, title, feed_url, logo_url, sum_pos in (
            await self.session.execute(top_time_statement)
        ).all():
            top_by_time.append(
                PodcastTimeRank(
                    feed_id=int(feed_id),
                    title=title,
                    logo_url=(logo_url or "").strip()
                    or choose_placeholder_url_stable(feed_url),
                    listened_seconds=int(sum_pos or 0),
                )
            )

        completed_by_feed: dict[int, tuple[int, int]] = {}
        for row in play_rows:
            feed_id = int(row.feed_id)
            completed, total = completed_by_feed.get(feed_id, (0, 0))
            total += 1
            if is_episode_completed(row.max_pos, row.max_total):
                completed += 1
            completed_by_feed[feed_id] = (completed, total)

        top_by_completed: list[PodcastCompletedRank] = []
        if completed_by_feed:
            feed_ids = sorted(completed_by_feed.keys())
            feeds = (
                (
                    await self.session.execute(
                        select(PodcastFeedModel).where(
                            PodcastFeedModel.id.in_(feed_ids)
                        )
                    )
                )
                .scalars()
                .all()
            )
            feed_map = {feed.id: feed for feed in feeds}
            ranked = sorted(
                (
                    (feed_id, completed, total)
                    for feed_id, (completed, total) in completed_by_feed.items()
                ),
                key=lambda item: (-item[1], -item[2], item[0]),
            )[:5]
            for feed_id, completed, total in ranked:
                feed = feed_map.get(feed_id)
                if feed is None:
                    continue
                top_by_completed.append(
                    PodcastCompletedRank(
                        feed_id=feed.id,
                        title=feed.title,
                        logo_url=(feed.logo_url or "").strip()
                        or choose_placeholder_url_stable(feed.feed_url),
                        completed_episodes=completed,
                        total_episodes=total,
                    )
                )

        return UserStatsPayload(
            highlights=UserStatsHighlights(
                listened_seconds=listened_seconds,
                completed_episodes=completed_episodes,
                followed_podcasts=followed_podcasts,
            ),
            top_by_time=top_by_time,
            top_by_completed=top_by_completed,
        )
