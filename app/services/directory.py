from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import quote

from sqlalchemy import Select, and_, func, or_, select

from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    EpisodeModel,
    PodcastFeedModel,
)
from app.db.models.user import UserModel
from app.schemas.directory import (
    EpisodeDataResponse,
    PodcastDataResponse,
    PodcastDirectoryItem,
    TagSummary,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings


@dataclass(frozen=True, slots=True)
class _FeedWithSubscribers:
    feed: PodcastFeedModel
    subscribers: int


class DirectoryService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def _normalized_base_url(self) -> str:
        cleaned = self.settings.base_url.strip()
        return f"{cleaned.rstrip('/')}/"

    def build_podcast_mygpo_link(self, feed_url: str) -> str:
        base = self._normalized_base_url()
        return f"{base}api/2/data/podcast.json?url={quote(feed_url, safe='')}"

    def build_episode_mygpo_link(self, feed_url: str, media_url: str) -> str:
        base = self._normalized_base_url()
        podcast = quote(feed_url, safe="")
        episode = quote(media_url, safe="")
        return f"{base}api/2/data/episode.json?podcast={podcast}&url={episode}"

    def _active_catalog_subscribers_stmt(self) -> Select[tuple[int, int]]:
        return (
            select(
                DeviceSubscriptionModel.feed_id,
                func.count(func.distinct(UserModel.id)).label("subscribers"),
            )
            .select_from(DeviceSubscriptionModel)
            .join(DeviceModel, DeviceModel.id == DeviceSubscriptionModel.device_pk)
            .join(UserModel, UserModel.id == DeviceModel.user_id)
            .where(DeviceSubscriptionModel.unsubscribed_at.is_(None))
            .group_by(DeviceSubscriptionModel.feed_id)
        )

    async def _fetch_catalog_feeds_with_subscribers(
        self,
        *,
        feed_url_filter: str | None = None,
        title_filter: str | None = None,
        limit: int | None = None,
        order_by_subscribers_desc: bool = False,
    ) -> list[_FeedWithSubscribers]:
        subscribers_subq = self._active_catalog_subscribers_stmt().subquery()
        stmt = select(PodcastFeedModel, subscribers_subq.c.subscribers).join(
            subscribers_subq, subscribers_subq.c.feed_id == PodcastFeedModel.id
        )

        if feed_url_filter is not None:
            stmt = stmt.where(PodcastFeedModel.feed_url == feed_url_filter)

        if title_filter is not None:
            needle = title_filter.strip().lower()
            pattern = f"%{needle}%"
            stmt = stmt.where(
                or_(
                    func.lower(PodcastFeedModel.title).like(pattern),
                    func.lower(PodcastFeedModel.feed_url).like(pattern),
                )
            )

        if order_by_subscribers_desc:
            stmt = stmt.order_by(
                subscribers_subq.c.subscribers.desc(),
                PodcastFeedModel.feed_url.asc(),
            )
        else:
            stmt = stmt.order_by(PodcastFeedModel.feed_url.asc())

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return [
            _FeedWithSubscribers(feed=feed, subscribers=int(subscribers or 0))
            for feed, subscribers in result.all()
        ]

    async def search_podcasts(
        self,
        query: str,
        *,
        limit: int = 50,
    ) -> list[PodcastDirectoryItem]:
        rows = await self._fetch_catalog_feeds_with_subscribers(
            title_filter=query,
            limit=limit,
        )
        return [self._to_directory_item(row) for row in rows]

    async def toplist(
        self,
        number: int,
    ) -> list[PodcastDirectoryItem]:
        rows = await self._fetch_catalog_feeds_with_subscribers(
            order_by_subscribers_desc=True,
            limit=number,
        )
        return [self._to_directory_item(row) for row in rows]

    async def get_podcast_data(self, feed_url: str) -> PodcastDataResponse | None:
        rows = await self._fetch_catalog_feeds_with_subscribers(
            feed_url_filter=feed_url,
            limit=1,
        )
        if not rows:
            return None
        row = rows[0]
        return PodcastDataResponse(
            url=row.feed.feed_url,
            title=row.feed.title,
            author=row.feed.author,
            description=row.feed.description,
            subscribers=row.subscribers,
            logo_url=row.feed.logo_url,
            website=row.feed.website,
            mygpo_link=self.build_podcast_mygpo_link(row.feed.feed_url),
        )

    async def get_episode_data(
        self,
        feed_url: str,
        media_url: str,
    ) -> EpisodeDataResponse | None:
        subscribers_subq = self._active_catalog_subscribers_stmt().subquery()
        stmt = (
            select(EpisodeModel, PodcastFeedModel, subscribers_subq.c.subscribers)
            .join(PodcastFeedModel, PodcastFeedModel.id == EpisodeModel.feed_id)
            .join(subscribers_subq, subscribers_subq.c.feed_id == PodcastFeedModel.id)
            .where(
                and_(
                    PodcastFeedModel.feed_url == feed_url,
                    EpisodeModel.episode_url == media_url,
                )
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if row is None:
            return None
        episode, feed, _subscribers = row
        return EpisodeDataResponse(
            title=episode.title,
            url=episode.episode_url,
            podcast_title=feed.title,
            podcast_url=feed.feed_url,
            description=episode.description,
            website=episode.website,
            released=episode.released_at,
            mygpo_link=self.build_episode_mygpo_link(
                feed.feed_url, episode.episode_url
            ),
        )

    async def list_tags(self, count: int) -> list[TagSummary]:
        rows = await self._fetch_catalog_feeds_with_subscribers(limit=None)
        counter: Counter[str] = Counter()
        for row in rows:
            categories = row.feed.categories or []
            for category in categories:
                cleaned = str(category).strip()
                if cleaned:
                    counter[cleaned] += 1
        most_common = counter.most_common(count)
        return [
            TagSummary(title=tag, tag=tag, usage=usage) for tag, usage in most_common
        ]

    async def list_tag_podcasts(
        self, tag: str, count: int
    ) -> list[PodcastDirectoryItem]:
        rows = await self._fetch_catalog_feeds_with_subscribers(limit=None)
        matching: list[_FeedWithSubscribers] = []
        for row in rows:
            categories = row.feed.categories or []
            if any(str(category).strip() == tag for category in categories):
                matching.append(row)
        matching.sort(key=lambda item: (-item.subscribers, item.feed.feed_url))
        return [self._to_directory_item(row) for row in matching[:count]]

    def _to_directory_item(self, row: _FeedWithSubscribers) -> PodcastDirectoryItem:
        return PodcastDirectoryItem(
            url=row.feed.feed_url,
            title=row.feed.title,
            author=row.feed.author,
            description=row.feed.description,
            website=row.feed.website,
            logo_url=row.feed.logo_url,
            subscribers=row.subscribers,
            mygpo_link=self.build_podcast_mygpo_link(row.feed.feed_url),
        )
