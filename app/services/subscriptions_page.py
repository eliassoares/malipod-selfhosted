from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import func, or_, select

from app.core.placeholders import choose_placeholder_url_stable
from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    EpisodeModel,
    PodcastFeedModel,
)
from app.schemas.subscriptions_page import SubscriptionFeedCard

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel

SortMode = Literal["recent", "oldest"]


@dataclass(slots=True)
class SubscriptionsQuery:
    q: str | None = None
    sort: SortMode = "recent"


class SubscriptionsPageService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_user_subscriptions(
        self,
        user: UserModel,
        *,
        query: SubscriptionsQuery,
    ) -> list[SubscriptionFeedCard]:
        search = (query.q or "").strip()

        last_episode_at = func.max(EpisodeModel.released_at)
        episode_count = func.count(EpisodeModel.id)

        statement = (
            select(
                PodcastFeedModel,
                episode_count.label("episode_count"),
                last_episode_at.label("last_episode_at"),
            )
            .join(
                DeviceSubscriptionModel,
                DeviceSubscriptionModel.feed_id == PodcastFeedModel.id,
            )
            .join(DeviceModel, DeviceModel.id == DeviceSubscriptionModel.device_pk)
            .outerjoin(EpisodeModel, EpisodeModel.feed_id == PodcastFeedModel.id)
            .where(
                DeviceModel.user_id == user.id,
                DeviceSubscriptionModel.unsubscribed_at.is_(None),
            )
            .group_by(PodcastFeedModel.id)
        )

        if search:
            candidate = f"%{search}%"
            statement = statement.where(
                or_(
                    PodcastFeedModel.title.ilike(candidate),
                    PodcastFeedModel.feed_url.ilike(candidate),
                )
            )

        null_bucket = last_episode_at.is_(None)
        if query.sort == "oldest":
            statement = statement.order_by(null_bucket.asc(), last_episode_at.asc())
        else:
            statement = statement.order_by(null_bucket.asc(), last_episode_at.desc())

        result = await self.session.execute(statement)
        items: list[SubscriptionFeedCard] = []
        for feed, raw_count, raw_last in result.all():
            logo_url = (feed.logo_url or "").strip() or choose_placeholder_url_stable(
                feed.feed_url
            )
            last_ep: datetime | None = None
            if raw_last is not None:
                last_ep = (
                    raw_last
                    if raw_last.tzinfo is not None
                    else raw_last.replace(tzinfo=UTC)
                )
            items.append(
                SubscriptionFeedCard(
                    feed_id=feed.id,
                    title=feed.title,
                    feed_url=feed.feed_url,
                    logo_url=logo_url,
                    description=feed.description,
                    episode_count=int(raw_count or 0),
                    last_episode_at=last_ep,
                )
            )
        return items
