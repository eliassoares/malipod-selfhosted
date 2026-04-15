from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    EpisodeActionModel,
    EpisodeModel,
    PodcastFeedModel,
)
from app.schemas.device import (
    DeviceSummary,
    DeviceUpdatesResponse,
    DeviceUpsertRequest,
    EpisodeUpdate,
    SubscriptionAdd,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel


class DeviceError(Exception):
    def __init__(
        self,
        code: Literal["device_not_found", "invalid_device_id", "invalid_since"],
    ) -> None:
        self.code = code
        super().__init__(code)


@dataclass(slots=True)
class SubscriptionSeed:
    url: str
    title: str
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    mygpo_link: str | None = None


class DeviceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _fetch_device_statement(
        self,
        statement: Select[tuple[DeviceModel]],
    ) -> DeviceModel | None:
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_device_for_user(self, user: UserModel, device_id: str) -> DeviceModel:
        device = await self._fetch_device_statement(
            select(DeviceModel)
            .options(
                selectinload(DeviceModel.subscriptions).selectinload(
                    DeviceSubscriptionModel.feed
                )
            )
            .where(
                DeviceModel.user_id == user.id,
                DeviceModel.device_id == device_id,
            )
        )
        if device is None:
            raise DeviceError("device_not_found")
        return device

    async def _active_subscription_count(self, device_pk: int) -> int:
        result = await self.session.execute(
            select(func.count(DeviceSubscriptionModel.id)).where(
                DeviceSubscriptionModel.device_pk == device_pk,
                DeviceSubscriptionModel.unsubscribed_at.is_(None),
            )
        )
        count = result.scalar_one()
        return int(count or 0)

    async def build_device_summary(self, device: DeviceModel) -> DeviceSummary:
        return DeviceSummary(
            id=device.device_id,
            caption=device.caption,
            type=device.device_type,
            subscriptions=await self._active_subscription_count(device.id),
        )

    async def upsert_device(
        self, user: UserModel, payload: DeviceUpsertRequest
    ) -> DeviceModel:
        device = await self._fetch_device_statement(
            select(DeviceModel).where(
                DeviceModel.user_id == user.id,
                DeviceModel.device_id == payload.device_id,
            )
        )
        now = datetime.now(UTC)
        if device is None:
            device = DeviceModel(
                user_id=user.id,
                device_id=payload.device_id,
                caption=payload.caption or "",
                device_type=payload.type or "other",
                created_at=now,
                updated_at=now,
            )
            self.session.add(device)
        else:
            if payload.caption is not None:
                device.caption = payload.caption
            if payload.type is not None:
                device.device_type = payload.type
            device.updated_at = now
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def list_devices_for_user(self, user: UserModel) -> list[DeviceSummary]:
        result = await self.session.execute(
            select(
                DeviceModel,
                func.count(DeviceSubscriptionModel.id).label("subscription_count"),
            )
            .outerjoin(
                DeviceSubscriptionModel,
                and_(
                    DeviceSubscriptionModel.device_pk == DeviceModel.id,
                    DeviceSubscriptionModel.unsubscribed_at.is_(None),
                ),
            )
            .where(DeviceModel.user_id == user.id)
            .group_by(DeviceModel.id)
            .order_by(DeviceModel.created_at.asc(), DeviceModel.id.asc())
        )
        summaries: list[DeviceSummary] = []
        for device, subscription_count in result.all():
            summaries.append(
                DeviceSummary(
                    id=device.device_id,
                    caption=device.caption,
                    type=device.device_type,
                    subscriptions=int(subscription_count or 0),
                )
            )
        return summaries

    async def _get_or_create_feed(
        self,
        *,
        url: str,
        title: str,
        description: str | None = None,
        website: str | None = None,
        logo_url: str | None = None,
        mygpo_link: str | None = None,
    ) -> PodcastFeedModel:
        result = await self.session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.feed_url == url)
        )
        feed = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if feed is None:
            feed = PodcastFeedModel(
                feed_url=url,
                title=title,
                description=description,
                website=website,
                logo_url=logo_url,
                mygpo_link=mygpo_link,
                created_at=now,
                updated_at=now,
            )
            self.session.add(feed)
            await self.session.flush()
            return feed

        feed.title = title
        feed.description = description
        feed.website = website
        feed.logo_url = logo_url
        feed.mygpo_link = mygpo_link
        feed.updated_at = now
        await self.session.flush()
        return feed

    async def replace_device_subscriptions(
        self,
        device: DeviceModel,
        subscriptions: Sequence[Mapping[str, object] | SubscriptionSeed],
    ) -> None:
        result = await self.session.execute(
            select(DeviceSubscriptionModel)
            .options(selectinload(DeviceSubscriptionModel.feed))
            .where(DeviceSubscriptionModel.device_pk == device.id)
        )
        existing = result.scalars().all()
        existing_by_url = {
            subscription.feed.feed_url: subscription for subscription in existing
        }
        seen_urls: set[str] = set()
        now = datetime.now(UTC)

        for raw in subscriptions:
            if isinstance(raw, SubscriptionSeed):
                subscription = raw
            else:
                subscription = SubscriptionSeed(
                    url=str(raw["url"]),
                    title=str(raw["title"]),
                    description=(
                        str(raw["description"])
                        if raw.get("description") is not None
                        else None
                    ),
                    website=(
                        str(raw["website"]) if raw.get("website") is not None else None
                    ),
                    logo_url=(
                        str(raw["logo_url"])
                        if raw.get("logo_url") is not None
                        else None
                    ),
                    mygpo_link=(
                        str(raw["mygpo_link"])
                        if raw.get("mygpo_link") is not None
                        else None
                    ),
                )
            feed = await self._get_or_create_feed(
                url=subscription.url,
                title=subscription.title,
                description=subscription.description,
                website=subscription.website,
                logo_url=subscription.logo_url,
                mygpo_link=subscription.mygpo_link,
            )
            current = existing_by_url.get(feed.feed_url)
            if current is None:
                self.session.add(
                    DeviceSubscriptionModel(
                        device_pk=device.id,
                        feed_id=feed.id,
                        subscribed_at=now,
                        unsubscribed_at=None,
                        updated_at=now,
                    )
                )
            else:
                current.unsubscribed_at = None
                current.updated_at = now
            seen_urls.add(feed.feed_url)

        for feed_url, current in existing_by_url.items():
            if feed_url not in seen_urls and current.unsubscribed_at is None:
                current.unsubscribed_at = now
                current.updated_at = now

        await self.session.commit()

    async def _get_or_create_episode(
        self,
        *,
        feed: PodcastFeedModel,
        episode_url: str,
        episode_title: str,
        description: str | None,
        website: str | None,
        mygpo_link: str | None,
        released_at: datetime,
    ) -> EpisodeModel:
        result = await self.session.execute(
            select(EpisodeModel).where(EpisodeModel.episode_url == episode_url)
        )
        episode = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if episode is None:
            episode = EpisodeModel(
                feed_id=feed.id,
                episode_url=episode_url,
                title=episode_title,
                description=description,
                website=website,
                mygpo_link=mygpo_link,
                released_at=released_at,
                created_at=now,
                updated_at=now,
            )
            self.session.add(episode)
            await self.session.flush()
            return episode

        episode.title = episode_title
        episode.description = description
        episode.website = website
        episode.mygpo_link = mygpo_link
        episode.released_at = released_at
        episode.updated_at = now
        await self.session.flush()
        return episode

    async def record_episode_update(
        self,
        *,
        user: UserModel,
        device: DeviceModel,
        feed_url: str,
        feed_title: str,
        episode_url: str,
        episode_title: str,
        status: str,
        occurred_at: datetime,
        action: dict[str, Any] | None = None,
        feed_description: str | None = None,
        feed_website: str | None = None,
        feed_logo_url: str | None = None,
        feed_mygpo_link: str | None = None,
        episode_description: str | None = None,
        episode_website: str | None = None,
        episode_mygpo_link: str | None = None,
        released_at: datetime | None = None,
    ) -> EpisodeActionModel:
        feed = await self._get_or_create_feed(
            url=feed_url,
            title=feed_title,
            description=feed_description,
            website=feed_website,
            logo_url=feed_logo_url,
            mygpo_link=feed_mygpo_link,
        )
        episode = await self._get_or_create_episode(
            feed=feed,
            episode_url=episode_url,
            episode_title=episode_title,
            description=episode_description,
            website=episode_website,
            mygpo_link=episode_mygpo_link,
            released_at=released_at or occurred_at,
        )
        result = await self.session.execute(
            select(EpisodeActionModel).where(
                EpisodeActionModel.user_id == user.id,
                EpisodeActionModel.episode_id == episode.id,
            )
        )
        episode_action = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if episode_action is None:
            episode_action = EpisodeActionModel(
                user_id=user.id,
                device_pk=device.id,
                episode_id=episode.id,
                status=status,
                action=None if status == "new" else action,
                occurred_at=occurred_at,
                updated_at=now,
            )
            self.session.add(episode_action)
        else:
            episode_action.device_pk = device.id
            episode_action.status = status
            episode_action.action = None if status == "new" else action
            episode_action.occurred_at = occurred_at
            episode_action.updated_at = now

        await self.session.commit()
        await self.session.refresh(episode_action)
        episode_action.occurred_at = self._ensure_utc(episode_action.occurred_at)
        episode_action.updated_at = self._ensure_utc(episode_action.updated_at)
        return episode_action

    async def get_updates_for_device(
        self,
        user: UserModel,
        device_id: str,
        since: int | None,
        include_actions: bool,
    ) -> DeviceUpdatesResponse:
        device = await self.get_device_for_user(user, device_id)
        threshold = datetime.fromtimestamp(since, tz=UTC) if since is not None else None

        active_result = await self.session.execute(
            select(DeviceSubscriptionModel)
            .options(selectinload(DeviceSubscriptionModel.feed))
            .where(
                DeviceSubscriptionModel.device_pk == device.id,
                DeviceSubscriptionModel.unsubscribed_at.is_(None),
            )
        )
        active_subscriptions = [
            subscription
            for subscription in active_result.scalars().all()
            if threshold is None
            or self._ensure_utc(subscription.subscribed_at) >= threshold
        ]
        added = [
            SubscriptionAdd(
                title=subscription.feed.title,
                url=subscription.feed.feed_url,
                description=subscription.feed.description,
                subscribers=1,
                logo_url=subscription.feed.logo_url,
                website=subscription.feed.website,
                mygpo_link=subscription.feed.mygpo_link,
            )
            for subscription in active_subscriptions
        ]

        removed_result = await self.session.execute(
            select(DeviceSubscriptionModel)
            .options(selectinload(DeviceSubscriptionModel.feed))
            .where(
                DeviceSubscriptionModel.device_pk == device.id,
                DeviceSubscriptionModel.unsubscribed_at.is_not(None),
            )
        )
        removed_subscriptions = [
            subscription
            for subscription in removed_result.scalars().all()
            if threshold is None
            or (
                subscription.unsubscribed_at is not None
                and self._ensure_utc(subscription.unsubscribed_at) >= threshold
            )
        ]
        removed = [subscription.feed.feed_url for subscription in removed_subscriptions]

        action_result = await self.session.execute(
            select(EpisodeActionModel)
            .options(
                selectinload(EpisodeActionModel.episode).selectinload(EpisodeModel.feed)
            )
            .where(
                EpisodeActionModel.user_id == user.id,
                or_(
                    EpisodeActionModel.device_pk == device.id,
                    EpisodeActionModel.device_pk.is_(None),
                ),
            )
            .order_by(EpisodeActionModel.occurred_at.asc())
        )
        action_models = [
            action_model
            for action_model in action_result.scalars().all()
            if threshold is None
            or self._ensure_utc(action_model.occurred_at) >= threshold
        ]
        updates = []
        for action_model in action_models:
            episode = action_model.episode
            feed = episode.feed
            updates.append(
                EpisodeUpdate(
                    title=episode.title,
                    url=episode.episode_url,
                    podcast_title=feed.title,
                    podcast_url=feed.feed_url,
                    description=episode.description,
                    website=episode.website,
                    mygpo_link=episode.mygpo_link,
                    released=episode.released_at,
                    status=action_model.status,
                    action=(
                        action_model.action
                        if include_actions and action_model.status != "new"
                        else None
                    ),
                )
            )

        timestamp_candidates = [datetime.now(UTC)]
        timestamp_candidates.extend(
            self._ensure_utc(subscription.updated_at)
            for subscription in active_subscriptions
        )
        timestamp_candidates.extend(
            self._ensure_utc(subscription.unsubscribed_at)
            for subscription in removed_subscriptions
            if subscription.unsubscribed_at is not None
        )
        timestamp_candidates.extend(
            self._ensure_utc(action_model.occurred_at) for action_model in action_models
        )
        latest_timestamp = max(timestamp_candidates)

        return DeviceUpdatesResponse(
            add=added,
            remove=removed,
            updates=updates,
            timestamp=int(latest_timestamp.timestamp()),
        )

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
