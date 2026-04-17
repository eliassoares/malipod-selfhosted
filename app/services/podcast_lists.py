from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.core.security import normalize_podcast_list_name, sanitize_subscription_url
from app.db.models.podcast import (
    PodcastFeedModel,
    PodcastListItemModel,
    PodcastListModel,
)
from app.db.models.user import UserModel
from app.schemas.podcast_list import (
    PodcastListEntry,
    PodcastListRenderPayload,
    PodcastListSummary,
)
from app.services.subscription_formats import (
    ImportedPodcastListEntry,
    SubscriptionFormatService,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class PodcastListError(Exception):
    def __init__(
        self,
        code: Literal["user_not_found", "list_not_found", "name_conflict"],
    ) -> None:
        self.code = code
        super().__init__(code)


@dataclass(slots=True)
class NormalizedPodcastListEntry:
    url: str
    title: str | None = None
    website: str | None = None
    description: str | None = None


class PodcastListService:
    def __init__(
        self,
        session: AsyncSession,
        base_url: str = "http://localhost:8000",
    ) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.format_service = SubscriptionFormatService()

    async def _fetch_user(self, username: str) -> UserModel | None:
        result = await self.session.execute(
            select(UserModel).where(
                UserModel.nickname == username,
                UserModel.deactivated_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def _fetch_list_statement(
        self,
        statement: Select[tuple[PodcastListModel]],
    ) -> PodcastListModel | None:
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def _get_list(self, user_id: int, listname: str) -> PodcastListModel:
        podcast_list = await self._fetch_list_statement(
            select(PodcastListModel)
            .options(
                selectinload(PodcastListModel.items).selectinload(
                    PodcastListItemModel.feed
                )
            )
            .where(
                PodcastListModel.user_id == user_id,
                PodcastListModel.name == listname,
            )
        )
        if podcast_list is None:
            raise PodcastListError("list_not_found")
        return podcast_list

    async def _get_or_create_feed(
        self,
        normalized: NormalizedPodcastListEntry,
    ) -> PodcastFeedModel:
        result = await self.session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.feed_url == normalized.url)
        )
        feed = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if feed is None:
            feed = PodcastFeedModel(
                feed_url=normalized.url,
                title=normalized.title or normalized.url,
                description=normalized.description,
                website=normalized.website,
                logo_url=None,
                mygpo_link=None,
                created_at=now,
                updated_at=now,
            )
            self.session.add(feed)
            await self.session.flush()
            return feed

        if normalized.title and feed.title == feed.feed_url:
            feed.title = normalized.title
        if normalized.website and not feed.website:
            feed.website = normalized.website
        if normalized.description and not feed.description:
            feed.description = normalized.description
        feed.updated_at = now
        await self.session.flush()
        return feed

    def _normalize_entries(
        self, entries: Sequence[ImportedPodcastListEntry]
    ) -> list[NormalizedPodcastListEntry]:
        deduped: OrderedDict[str, NormalizedPodcastListEntry] = OrderedDict()
        for entry in entries:
            sanitized = sanitize_subscription_url(entry.url)
            if not sanitized or sanitized in deduped:
                continue
            title = entry.title.strip() if entry.title else None
            website = (
                sanitize_subscription_url(entry.website) if entry.website else None
            )
            description = entry.description.strip() if entry.description else None
            deduped[sanitized] = NormalizedPodcastListEntry(
                url=sanitized,
                title=title,
                website=website or None,
                description=description,
            )
        return list(deduped.values())

    @staticmethod
    def _user_id(user: UserModel) -> int:
        if user.id is None:
            raise ValueError("user must be persistent before managing podcast lists")
        return user.id

    @staticmethod
    def _user_nickname(user: UserModel) -> str:
        if not user.nickname:
            raise ValueError("user nickname could not be resolved")
        return user.nickname

    def _build_web_url(self, username: str, listname: str) -> str:
        return f"{self.base_url}/user/{username}/lists/{listname}"

    def _build_resource_url(
        self, username: str, listname: str, format_name: str
    ) -> str:
        return f"/api/2/lists/{username}/list/{listname}.{format_name}"

    def _build_list_entry(self, item: PodcastListItemModel) -> PodcastListEntry:
        return PodcastListEntry(
            url=item.feed.feed_url,
            title=item.feed.title,
            description=item.feed.description,
            website=item.feed.website,
            logo_url=item.feed.logo_url,
            mygpo_link=item.feed.mygpo_link,
        )

    async def list_summaries(self, username: str) -> list[PodcastListSummary]:
        user = await self._fetch_user(username)
        if user is None:
            raise PodcastListError("user_not_found")
        result = await self.session.execute(
            select(PodcastListModel)
            .where(PodcastListModel.user_id == user.id)
            .order_by(PodcastListModel.created_at.asc(), PodcastListModel.name.asc())
        )
        return [
            PodcastListSummary(
                title=item.title,
                name=item.name,
                web=self._build_web_url(user.nickname, item.name),
            )
            for item in result.scalars().all()
        ]

    async def get_document(
        self, username: str, listname: str, format_name: str
    ) -> PodcastListRenderPayload:
        user = await self._fetch_user(username)
        if user is None:
            raise PodcastListError("user_not_found")
        podcast_list = await self._get_list(user.id, listname)
        return PodcastListRenderPayload(
            title=podcast_list.title,
            name=podcast_list.name,
            items=[self._build_list_entry(item) for item in podcast_list.items],
            format=format_name,
        )

    async def create_list(
        self,
        user: UserModel,
        *,
        title: str,
        format_name: str,
        body: bytes,
    ) -> str:
        user_id = self._user_id(user)
        username = self._user_nickname(user)
        name = normalize_podcast_list_name(title)
        existing = await self._fetch_list_statement(
            select(PodcastListModel).where(
                PodcastListModel.user_id == user_id,
                PodcastListModel.name == name,
            )
        )
        if existing is not None:
            raise PodcastListError("name_conflict")

        entries = self.format_service.parse_list_upload(format_name, body)
        normalized_entries = self._normalize_entries(entries)
        now = datetime.now(UTC)
        podcast_list = PodcastListModel(
            user_id=user_id,
            title=title,
            name=name,
            created_at=now,
            updated_at=now,
        )
        self.session.add(podcast_list)
        await self.session.flush()

        for position, normalized in enumerate(normalized_entries):
            feed = await self._get_or_create_feed(normalized)
            self.session.add(
                PodcastListItemModel(
                    list_id=podcast_list.id,
                    feed_id=feed.id,
                    position=position,
                    created_at=now,
                    updated_at=now,
                )
            )
        await self.session.commit()
        return self._build_resource_url(username, name, format_name)

    async def update_list(
        self,
        user: UserModel,
        *,
        listname: str,
        format_name: str,
        body: bytes,
    ) -> None:
        podcast_list = await self._get_list(self._user_id(user), listname)
        entries = self.format_service.parse_list_upload(format_name, body)
        normalized_entries = self._normalize_entries(entries)
        now = datetime.now(UTC)

        existing_items = list(podcast_list.items)
        for item in existing_items:
            await self.session.delete(item)
        await self.session.flush()

        for position, normalized in enumerate(normalized_entries):
            feed = await self._get_or_create_feed(normalized)
            self.session.add(
                PodcastListItemModel(
                    list_id=podcast_list.id,
                    feed_id=feed.id,
                    position=position,
                    created_at=now,
                    updated_at=now,
                )
            )
        podcast_list.updated_at = now
        await self.session.commit()
        self.session.expire(podcast_list)

    async def delete_list(self, user: UserModel, listname: str) -> None:
        podcast_list = await self._get_list(self._user_id(user), listname)
        await self.session.delete(podcast_list)
        await self.session.commit()
