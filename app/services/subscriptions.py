from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.core.placeholders import choose_placeholder_url_random
from app.core.security import sanitize_subscription_url
from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    PodcastFeedModel,
    SubscriptionChangeEventModel,
)
from app.schemas.subscription import (
    SubscriptionDeltaResponse,
    SubscriptionDeltaUploadResponse,
    SubscriptionItem,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel
    from app.services.subscription_formats import ImportedSubscription


class SubscriptionError(Exception):
    def __init__(
        self,
        code: Literal["device_not_found", "conflicting_delta"],
    ) -> None:
        self.code = code
        super().__init__(code)


@dataclass(slots=True)
class NormalizedImportedSubscription:
    url: str
    title: str | None = None


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _fetch_device_statement(
        self,
        statement: Select[tuple[DeviceModel]],
    ) -> DeviceModel | None:
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def _get_device(
        self, user: UserModel, device_id: str, *, create_if_missing: bool = False
    ) -> DeviceModel:
        device = await self._fetch_device_statement(
            select(DeviceModel)
            .options(
                selectinload(DeviceModel.subscriptions).selectinload(
                    DeviceSubscriptionModel.feed
                )
            )
            .where(DeviceModel.user_id == user.id, DeviceModel.device_id == device_id)
        )
        if device is not None:
            return device
        if not create_if_missing:
            raise SubscriptionError("device_not_found")

        now = datetime.now(UTC)
        device = DeviceModel(
            user_id=user.id,
            device_id=device_id,
            caption="",
            device_type="other",
            created_at=now,
            updated_at=now,
        )
        self.session.add(device)
        await self.session.flush()
        return device

    async def _get_or_create_feed(
        self,
        url: str,
        *,
        title: str | None = None,
    ) -> PodcastFeedModel:
        result = await self.session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.feed_url == url)
        )
        feed = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if feed is None:
            feed = PodcastFeedModel(
                feed_url=url,
                title=title or url,
                description=None,
                website=None,
                logo_url=choose_placeholder_url_random(),
                mygpo_link=None,
                created_at=now,
                updated_at=now,
            )
            self.session.add(feed)
            await self.session.flush()
            return feed

        if title and feed.title == feed.feed_url:
            feed.title = title
            feed.updated_at = now
            await self.session.flush()
        return feed

    async def _record_event(
        self,
        device_pk: int,
        feed_url: str,
        operation: str,
    ) -> None:
        self.session.add(
            SubscriptionChangeEventModel(
                device_pk=device_pk,
                feed_url=feed_url,
                operation=operation,
                created_at=datetime.now(UTC),
            )
        )
        await self.session.flush()

    async def _current_timestamp(self, device_pk: int) -> int:
        result = await self.session.execute(
            select(func.max(SubscriptionChangeEventModel.id)).where(
                SubscriptionChangeEventModel.device_pk == device_pk
            )
        )
        timestamp = result.scalar_one()
        return int(timestamp or 0)

    async def _current_timestamp_for_user(self, user: UserModel) -> int:
        result = await self.session.execute(
            select(func.max(SubscriptionChangeEventModel.id))
            .join(DeviceModel, DeviceModel.id == SubscriptionChangeEventModel.device_pk)
            .where(DeviceModel.user_id == user.id)
        )
        timestamp = result.scalar_one()
        return int(timestamp or 0)

    async def _active_urls_for_user(self, user: UserModel) -> set[str]:
        result = await self.session.execute(
            select(PodcastFeedModel.feed_url)
            .select_from(DeviceSubscriptionModel)
            .join(
                PodcastFeedModel,
                PodcastFeedModel.id == DeviceSubscriptionModel.feed_id,
            )
            .join(DeviceModel, DeviceModel.id == DeviceSubscriptionModel.device_pk)
            .where(
                DeviceModel.user_id == user.id,
                DeviceSubscriptionModel.unsubscribed_at.is_(None),
            )
            .distinct()
        )
        return set(result.scalars().all())

    def _normalize_imports(
        self, subscriptions: Sequence[ImportedSubscription]
    ) -> list[NormalizedImportedSubscription]:
        deduped: OrderedDict[str, NormalizedImportedSubscription] = OrderedDict()
        for subscription in subscriptions:
            sanitized = sanitize_subscription_url(subscription.url)
            if not sanitized or sanitized in deduped:
                continue
            title = subscription.title.strip() if subscription.title else None
            deduped[sanitized] = NormalizedImportedSubscription(
                url=sanitized,
                title=title,
            )
        return list(deduped.values())

    def _normalize_url_list(
        self, urls: Sequence[str]
    ) -> tuple[list[str], list[tuple[str, str]]]:
        deduped: OrderedDict[str, None] = OrderedDict()
        rewritten: list[tuple[str, str]] = []
        for original in urls:
            sanitized = sanitize_subscription_url(original)
            if sanitized != original:
                rewritten.append((original, sanitized))
            if sanitized and sanitized not in deduped:
                deduped[sanitized] = None
        return list(deduped.keys()), rewritten

    async def list_device_subscriptions(
        self, user: UserModel, device_id: str
    ) -> list[SubscriptionItem]:
        device = await self._get_device(user, device_id)
        if user.centralize_sync:
            return await self.list_account_subscriptions(user)
        result = await self.session.execute(
            select(DeviceSubscriptionModel)
            .options(selectinload(DeviceSubscriptionModel.feed))
            .where(
                DeviceSubscriptionModel.device_pk == device.id,
                DeviceSubscriptionModel.unsubscribed_at.is_(None),
            )
            .order_by(
                DeviceSubscriptionModel.subscribed_at.asc(),
                DeviceSubscriptionModel.id.asc(),
            )
        )
        rows = result.scalars().all()
        return [
            SubscriptionItem(
                url=row.feed.feed_url,
                title=row.feed.title,
                description=row.feed.description,
                website=row.feed.website,
                logo_url=row.feed.logo_url,
                mygpo_link=row.feed.mygpo_link,
            )
            for row in rows
        ]

    async def list_account_subscriptions(
        self,
        user: UserModel,
    ) -> list[SubscriptionItem]:
        result = await self.session.execute(
            select(DeviceSubscriptionModel)
            .options(selectinload(DeviceSubscriptionModel.feed))
            .join(DeviceModel, DeviceModel.id == DeviceSubscriptionModel.device_pk)
            .where(
                DeviceModel.user_id == user.id,
                DeviceSubscriptionModel.unsubscribed_at.is_(None),
            )
            .order_by(
                DeviceSubscriptionModel.subscribed_at.asc(),
                DeviceSubscriptionModel.id.asc(),
            )
        )
        deduped: OrderedDict[str, SubscriptionItem] = OrderedDict()
        for row in result.scalars().all():
            if row.feed.feed_url in deduped:
                continue
            deduped[row.feed.feed_url] = SubscriptionItem(
                url=row.feed.feed_url,
                title=row.feed.title,
                description=row.feed.description,
                website=row.feed.website,
                logo_url=row.feed.logo_url,
                mygpo_link=row.feed.mygpo_link,
            )
        return list(deduped.values())

    async def replace_device_subscriptions(
        self,
        user: UserModel,
        device_id: str,
        subscriptions: Sequence[ImportedSubscription],
    ) -> None:
        device = await self._get_device(user, device_id, create_if_missing=True)
        normalized = self._normalize_imports(subscriptions)
        result = await self.session.execute(
            select(DeviceSubscriptionModel)
            .options(selectinload(DeviceSubscriptionModel.feed))
            .where(DeviceSubscriptionModel.device_pk == device.id)
        )
        existing = result.scalars().all()
        existing_by_url = {row.feed.feed_url: row for row in existing}
        active_urls: set[str] = set()
        now = datetime.now(UTC)

        for imported in normalized:
            feed = await self._get_or_create_feed(imported.url, title=imported.title)
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
                await self.session.flush()
                await self._record_event(device.id, feed.feed_url, "add")
            elif current.unsubscribed_at is not None:
                current.subscribed_at = now
                current.unsubscribed_at = None
                current.updated_at = now
                await self.session.flush()
                await self._record_event(device.id, feed.feed_url, "add")
            active_urls.add(feed.feed_url)

        for feed_url, current in existing_by_url.items():
            if feed_url not in active_urls and current.unsubscribed_at is None:
                current.unsubscribed_at = now
                current.updated_at = now
                await self.session.flush()
                await self._record_event(device.id, feed_url, "remove")

        device.updated_at = now
        await self.session.commit()

    async def apply_delta(
        self,
        user: UserModel,
        device_id: str,
        add_urls: Sequence[str],
        remove_urls: Sequence[str],
    ) -> SubscriptionDeltaUploadResponse:
        device = await self._get_device(user, device_id)
        add, add_rewrites = self._normalize_url_list(add_urls)
        remove, remove_rewrites = self._normalize_url_list(remove_urls)
        if set(add) & set(remove):
            raise SubscriptionError("conflicting_delta")

        result = await self.session.execute(
            select(DeviceSubscriptionModel)
            .options(selectinload(DeviceSubscriptionModel.feed))
            .where(DeviceSubscriptionModel.device_pk == device.id)
        )
        existing = result.scalars().all()
        existing_by_url = {row.feed.feed_url: row for row in existing}
        now = datetime.now(UTC)

        for url in add:
            feed = await self._get_or_create_feed(url, title=url)
            current = existing_by_url.get(url)
            if current is None:
                current = DeviceSubscriptionModel(
                    device_pk=device.id,
                    feed_id=feed.id,
                    subscribed_at=now,
                    unsubscribed_at=None,
                    updated_at=now,
                )
                self.session.add(current)
                existing_by_url[url] = current
                await self.session.flush()
                await self._record_event(device.id, url, "add")
            elif current.unsubscribed_at is not None:
                current.subscribed_at = now
                current.unsubscribed_at = None
                current.updated_at = now
                await self.session.flush()
                await self._record_event(device.id, url, "add")

        for url in remove:
            current = existing_by_url.get(url)
            if current is None or current.unsubscribed_at is not None:
                continue
            current.unsubscribed_at = now
            current.updated_at = now
            await self.session.flush()
            await self._record_event(device.id, url, "remove")

        device.updated_at = now
        await self.session.commit()
        return SubscriptionDeltaUploadResponse(
            timestamp=await self._current_timestamp(device.id),
            update_urls=add_rewrites + remove_rewrites,
        )

    async def get_changes(
        self,
        user: UserModel,
        device_id: str,
        since: int | None,
    ) -> SubscriptionDeltaResponse:
        device = await self._get_device(user, device_id)
        query_since = since or 0
        if user.centralize_sync:
            result = await self.session.execute(
                select(SubscriptionChangeEventModel)
                .join(
                    DeviceModel,
                    DeviceModel.id == SubscriptionChangeEventModel.device_pk,
                )
                .where(
                    DeviceModel.user_id == user.id,
                    SubscriptionChangeEventModel.id > query_since,
                )
                .order_by(SubscriptionChangeEventModel.id.asc())
            )
        else:
            result = await self.session.execute(
                select(SubscriptionChangeEventModel)
                .where(
                    SubscriptionChangeEventModel.device_pk == device.id,
                    SubscriptionChangeEventModel.id > query_since,
                )
                .order_by(SubscriptionChangeEventModel.id.asc())
            )
        net_changes: OrderedDict[str, str] = OrderedDict()
        for event in result.scalars().all():
            if event.feed_url in net_changes:
                del net_changes[event.feed_url]
            net_changes[event.feed_url] = event.operation

        add = [url for url, operation in net_changes.items() if operation == "add"]
        remove_candidates = [
            url for url, operation in net_changes.items() if operation == "remove"
        ]
        if user.centralize_sync:
            active_urls = await self._active_urls_for_user(user)
            remove = [url for url in remove_candidates if url not in active_urls]
            timestamp = await self._current_timestamp_for_user(user)
        else:
            remove = remove_candidates
            timestamp = await self._current_timestamp(device.id)
        return SubscriptionDeltaResponse(
            add=add,
            remove=remove,
            timestamp=timestamp,
        )
