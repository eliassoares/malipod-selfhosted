from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import select

from app.core.placeholders import choose_placeholder_url_stable
from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    EpisodeModel,
    PodcastFeedModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel

SortMode = Literal["recent", "oldest"]


@dataclass(slots=True)
class EpisodeCard:
    id: int
    title: str
    released_at: datetime
    logo_url: str
    description: str | None


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

    async def list_episodes(
        self,
        *,
        feed_id: int,
        sort: SortMode,
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

        result = await self.session.execute(statement)
        episodes = result.scalars().all()
        cards: list[EpisodeCard] = []
        for episode in episodes:
            logo_url = (
                episode.logo_url or ""
            ).strip() or choose_placeholder_url_stable(episode.episode_url)
            cards.append(
                EpisodeCard(
                    id=episode.id,
                    title=episode.title,
                    released_at=_normalize_timestamp(episode.released_at),
                    logo_url=logo_url,
                    description=episode.description,
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
