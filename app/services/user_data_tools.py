from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select

from app.db.models.device import DeviceModel
from app.db.models.device_sync_group import DeviceSyncGroupModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    EpisodeActionEventModel,
    EpisodeActionModel,
    EpisodeModel,
    EpisodePlaylistItemModel,
    EpisodePlaylistModel,
    FavoriteEpisodeModel,
    PodcastFeedModel,
    PodcastListItemModel,
    PodcastListModel,
    SubscriptionChangeEventModel,
)
from app.db.models.session import AuthenticatedSessionModel
from app.db.models.settings import (
    AccountSettingModel,
    DeviceSettingModel,
    EpisodeSettingModel,
    PodcastSettingModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel
    from app.schemas.user_data_tools import UserDataSnapshot


class UserDataToolsError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _as_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


class UserDataToolsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def export_snapshot(self, user: UserModel) -> dict[str, Any]:
        devices = await self._export_devices(user)
        device_pks = [device["device_pk"] for device in devices]

        account_settings = await self._export_account_settings(user)
        device_settings = await self._export_device_settings(user)
        podcast_lists = await self._export_podcast_lists(user)
        podcast_list_items = await self._export_podcast_list_items(user)

        device_subscriptions = await self._export_device_subscriptions(user)

        episode_actions = await self._export_episode_actions(user)
        favorite_episodes = await self._export_favorites(user)
        episode_action_events = await self._export_episode_action_events(user)
        subscription_change_events = await self._export_subscription_change_events(
            device_pks=device_pks,
        )

        podcast_settings = await self._export_podcast_settings(user)
        episode_settings = await self._export_episode_settings(user)
        episode_playlists = await self._export_episode_playlists(user)
        episode_playlist_items = await self._export_episode_playlist_items(user)

        feed_urls, episode_urls = await self._collect_catalog_references(
            device_subscriptions=device_subscriptions,
            podcast_list_items=podcast_list_items,
            podcast_settings=podcast_settings,
            episode_settings=episode_settings,
            favorite_episodes=favorite_episodes,
            episode_actions=episode_actions,
            episode_action_events=episode_action_events,
            episode_playlist_items=episode_playlist_items,
        )
        podcast_feeds, episodes = await self._export_catalog(feed_urls, episode_urls)

        return {
            "users": [
                {
                    "nickname": user.nickname,
                    "email": user.email,
                    "picture_url": user.picture_url,
                    "language_preference": user.language_preference,
                    "created_at": _as_iso(user.created_at),
                    "updated_at": _as_iso(user.updated_at),
                    "accessed_at": _as_iso(user.accessed_at),
                    "deactivated_at": _as_iso(user.deactivated_at),
                }
            ],
            "account_settings": account_settings,
            "devices": [
                {key: value for key, value in device.items() if key != "device_pk"}
                for device in devices
            ],
            "device_settings": device_settings,
            "podcast_feeds": podcast_feeds,
            "episodes": episodes,
            "device_subscriptions": device_subscriptions,
            "episode_actions": episode_actions,
            "favorite_episodes": favorite_episodes,
            "subscription_change_events": subscription_change_events,
            "episode_action_events": episode_action_events,
            "podcast_lists": podcast_lists,
            "podcast_list_items": podcast_list_items,
            "podcast_settings": podcast_settings,
            "episode_settings": episode_settings,
            "episode_playlists": episode_playlists,
            "episode_playlist_items": episode_playlist_items,
        }

    async def import_snapshot(
        self, user: UserModel, snapshot: UserDataSnapshot
    ) -> None:
        if snapshot.users:
            row = snapshot.users[0]
            if row.email != user.email or row.nickname != user.nickname:
                raise UserDataToolsError("snapshot_user_mismatch")

        # Phase 1: global catalog (podcast_feeds → episodes)
        await self._import_podcast_feeds(snapshot)
        await self.session.flush()

        feed_urls: set[str] = (
            {r.feed_url for r in snapshot.podcast_feeds}
            | {r.feed_url for r in snapshot.episodes}
            | {r.feed_url for r in snapshot.device_subscriptions}
            | {r.feed_url for r in snapshot.podcast_settings}
            | {r.feed_url for r in snapshot.podcast_list_items}
        )
        feed_id_map = await self._feed_id_map(feed_urls)

        await self._import_episodes(snapshot, feed_id_map)
        await self.session.flush()

        episode_urls: set[str] = (
            {r.episode_url for r in snapshot.episodes}
            | {r.episode_url for r in snapshot.episode_settings}
            | {r.episode_url for r in snapshot.episode_actions}
            | {r.episode_url for r in snapshot.favorite_episodes}
            | {r.episode_url for r in snapshot.episode_action_events}
            | {r.episode_url for r in snapshot.episode_playlist_items}
        )
        episode_id_map = await self._episode_id_map(episode_urls)

        # Phase 2: user devices
        await self._import_devices(user, snapshot)
        await self.session.flush()

        device_pk_map = await self._device_pk_map(user.id)
        await self._rebuild_device_sync_groups(user, snapshot)

        # Phase 3: settings
        await self._import_account_settings(user, snapshot)
        await self._import_device_settings(user, snapshot, device_pk_map)
        await self._import_podcast_settings(user, snapshot, feed_id_map)
        await self._import_episode_settings(user, snapshot, episode_id_map)

        # Phase 4: podcast lists
        await self._import_podcast_lists(user, snapshot)
        await self.session.flush()

        list_id_map = await self._list_id_map(user.id)
        await self._import_podcast_list_items(user, snapshot, feed_id_map, list_id_map)

        # Phase 5: activity data
        await self._import_device_subscriptions(
            user, snapshot, device_pk_map, feed_id_map
        )
        await self._import_episode_actions(
            user, snapshot, device_pk_map, episode_id_map
        )
        await self._import_favorite_episodes(user, snapshot, episode_id_map)
        await self._import_subscription_change_events(user, snapshot, device_pk_map)
        await self._import_episode_action_events(user, snapshot, episode_id_map)

        # Phase 6: episode playlists
        await self._import_episode_playlists(user, snapshot)
        await self.session.flush()
        await self._import_episode_playlist_items(user, snapshot, episode_id_map)

        await self.session.commit()

    async def delete_user_data(self, user: UserModel) -> None:
        await self._delete_user_data_in_tx(user)
        await self.session.commit()

    async def delete_user_account(self, user: UserModel) -> None:
        await self._delete_user_data_in_tx(user)
        await self.session.delete(user)
        await self.session.commit()

    async def _delete_user_data_in_tx(self, user: UserModel) -> None:
        device_ids_result = await self.session.execute(
            select(DeviceModel.id).where(DeviceModel.user_id == user.id)
        )
        device_pks = [row[0] for row in device_ids_result.all()]

        if device_pks:
            await self.session.execute(
                delete(DeviceSubscriptionModel).where(
                    DeviceSubscriptionModel.device_pk.in_(device_pks)
                )
            )
            await self.session.execute(
                delete(SubscriptionChangeEventModel).where(
                    SubscriptionChangeEventModel.device_pk.in_(device_pks)
                )
            )

        await self.session.execute(
            delete(DeviceSettingModel).where(DeviceSettingModel.user_id == user.id)
        )
        await self.session.execute(
            delete(PodcastSettingModel).where(PodcastSettingModel.user_id == user.id)
        )
        await self.session.execute(
            delete(EpisodeSettingModel).where(EpisodeSettingModel.user_id == user.id)
        )
        await self.session.execute(
            delete(PodcastListModel).where(PodcastListModel.user_id == user.id)
        )
        await self.session.execute(
            delete(EpisodeActionModel).where(EpisodeActionModel.user_id == user.id)
        )
        await self.session.execute(
            delete(FavoriteEpisodeModel).where(FavoriteEpisodeModel.user_id == user.id)
        )
        await self.session.execute(
            delete(EpisodeActionEventModel).where(
                EpisodeActionEventModel.user_id == user.id
            )
        )
        await self.session.execute(
            delete(AccountSettingModel).where(AccountSettingModel.user_id == user.id)
        )
        await self.session.execute(
            delete(AuthenticatedSessionModel).where(
                AuthenticatedSessionModel.user_id == user.id
            )
        )
        await self.session.execute(
            delete(DeviceSyncGroupModel).where(DeviceSyncGroupModel.user_id == user.id)
        )
        await self.session.execute(
            delete(DeviceModel).where(DeviceModel.user_id == user.id)
        )

    async def _export_devices(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.user_id == user.id)
        )
        rows = result.scalars().all()
        return [
            {
                "device_pk": row.id,
                "device_id": row.device_id,
                "caption": row.caption,
                "device_type": row.device_type,
                "sync_group": f"group-{row.sync_group_id}"
                if row.sync_group_id is not None
                else None,
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row in rows
        ]

    async def _export_account_settings(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(AccountSettingModel).where(AccountSettingModel.user_id == user.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return []
        return [
            {
                "settings": dict(row.settings or {}),
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
        ]

    async def _export_device_settings(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(DeviceSettingModel, DeviceModel.device_id)
            .join(DeviceModel, DeviceSettingModel.device_pk == DeviceModel.id)
            .where(DeviceSettingModel.user_id == user.id)
        )
        return [
            {
                "device_id": device_id,
                "settings": dict(row.settings or {}),
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row, device_id in result.all()
        ]

    async def _export_podcast_settings(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(PodcastSettingModel, PodcastFeedModel.feed_url)
            .join(PodcastFeedModel, PodcastSettingModel.feed_id == PodcastFeedModel.id)
            .where(PodcastSettingModel.user_id == user.id)
        )
        return [
            {
                "feed_url": feed_url,
                "settings": dict(row.settings or {}),
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row, feed_url in result.all()
        ]

    async def _export_episode_settings(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(EpisodeSettingModel, EpisodeModel.episode_url)
            .join(EpisodeModel, EpisodeSettingModel.episode_id == EpisodeModel.id)
            .where(EpisodeSettingModel.user_id == user.id)
        )
        return [
            {
                "episode_url": episode_url,
                "settings": dict(row.settings or {}),
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row, episode_url in result.all()
        ]

    async def _export_podcast_lists(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(PodcastListModel).where(PodcastListModel.user_id == user.id)
        )
        rows = result.scalars().all()
        return [
            {
                "title": row.title,
                "name": row.name,
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row in rows
        ]

    async def _export_podcast_list_items(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(
                PodcastListItemModel,
                PodcastListModel.name,
                PodcastFeedModel.feed_url,
            )
            .join(PodcastListModel, PodcastListItemModel.list_id == PodcastListModel.id)
            .join(PodcastFeedModel, PodcastListItemModel.feed_id == PodcastFeedModel.id)
            .where(PodcastListModel.user_id == user.id)
        )
        return [
            {
                "list_name": list_name,
                "feed_url": feed_url,
                "position": row.position,
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row, list_name, feed_url in result.all()
        ]

    async def _export_device_subscriptions(
        self, user: UserModel
    ) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(
                DeviceSubscriptionModel,
                DeviceModel.device_id,
                PodcastFeedModel.feed_url,
            )
            .join(DeviceModel, DeviceSubscriptionModel.device_pk == DeviceModel.id)
            .join(
                PodcastFeedModel,
                DeviceSubscriptionModel.feed_id == PodcastFeedModel.id,
            )
            .where(DeviceModel.user_id == user.id)
        )
        return [
            {
                "device_id": device_id,
                "feed_url": feed_url,
                "subscribed_at": _as_iso(row.subscribed_at),
                "unsubscribed_at": _as_iso(row.unsubscribed_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row, device_id, feed_url in result.all()
        ]

    async def _export_episode_actions(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(EpisodeActionModel, EpisodeModel.episode_url, DeviceModel.device_id)
            .join(EpisodeModel, EpisodeActionModel.episode_id == EpisodeModel.id)
            .outerjoin(DeviceModel, EpisodeActionModel.device_pk == DeviceModel.id)
            .where(EpisodeActionModel.user_id == user.id)
        )
        return [
            {
                "episode_url": episode_url,
                "status": row.status,
                "action": row.action,
                "device_id": device_id,
                "occurred_at": _as_iso(row.occurred_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row, episode_url, device_id in result.all()
        ]

    async def _export_favorites(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(FavoriteEpisodeModel, EpisodeModel.episode_url)
            .join(EpisodeModel, FavoriteEpisodeModel.episode_id == EpisodeModel.id)
            .where(FavoriteEpisodeModel.user_id == user.id)
        )
        return [
            {
                "episode_url": episode_url,
                "favorited_at": _as_iso(row.favorited_at),
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row, episode_url in result.all()
        ]

    async def _export_subscription_change_events(
        self,
        *,
        device_pks: list[int],
    ) -> list[dict[str, Any]]:
        if not device_pks:
            return []
        result = await self.session.execute(
            select(SubscriptionChangeEventModel, DeviceModel.device_id)
            .join(DeviceModel, SubscriptionChangeEventModel.device_pk == DeviceModel.id)
            .where(SubscriptionChangeEventModel.device_pk.in_(device_pks))
        )
        return [
            {
                "device_id": device_id,
                "feed_url": row.feed_url,
                "operation": row.operation,
                "created_at": _as_iso(row.created_at),
            }
            for row, device_id in result.all()
        ]

    async def _export_episode_action_events(
        self, user: UserModel
    ) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(EpisodeActionEventModel).where(
                EpisodeActionEventModel.user_id == user.id
            )
        )
        rows = result.scalars().all()
        return [
            {
                "episode_url": row.episode_url,
                "podcast_url": row.podcast_url,
                "device_id": row.device_id,
                "action": row.action,
                "occurred_at": _as_iso(row.occurred_at),
                "started": row.started,
                "position": row.position,
                "total": row.total,
                "created_at": _as_iso(row.created_at),
            }
            for row in rows
        ]

    async def _collect_catalog_references(
        self,
        *,
        device_subscriptions: list[dict[str, Any]],
        podcast_list_items: list[dict[str, Any]],
        podcast_settings: list[dict[str, Any]],
        episode_settings: list[dict[str, Any]],
        favorite_episodes: list[dict[str, Any]],
        episode_actions: list[dict[str, Any]],
        episode_action_events: list[dict[str, Any]],
        episode_playlist_items: list[dict[str, Any]] | None = None,
    ) -> tuple[set[str], set[str]]:
        feed_urls: set[str] = set()
        episode_urls: set[str] = set()
        feed_urls.update(item["feed_url"] for item in device_subscriptions)
        feed_urls.update(item["feed_url"] for item in podcast_list_items)
        feed_urls.update(item["feed_url"] for item in podcast_settings)
        episode_urls.update(item["episode_url"] for item in episode_settings)
        episode_urls.update(item["episode_url"] for item in favorite_episodes)
        episode_urls.update(item["episode_url"] for item in episode_actions)
        episode_urls.update(item["episode_url"] for item in episode_action_events)
        if episode_playlist_items:
            episode_urls.update(item["episode_url"] for item in episode_playlist_items)

        if episode_urls:
            result = await self.session.execute(
                select(EpisodeModel.episode_url, PodcastFeedModel.feed_url)
                .join(PodcastFeedModel, EpisodeModel.feed_id == PodcastFeedModel.id)
                .where(EpisodeModel.episode_url.in_(episode_urls))
            )
            for episode_url, feed_url in result.all():
                episode_urls.add(episode_url)
                feed_urls.add(feed_url)

        return feed_urls, episode_urls

    async def _export_catalog(
        self, feed_urls: set[str], episode_urls: set[str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        feeds: list[dict[str, Any]] = []
        episodes: list[dict[str, Any]] = []

        if feed_urls:
            feed_result = await self.session.execute(
                select(PodcastFeedModel).where(PodcastFeedModel.feed_url.in_(feed_urls))
            )
            for row in feed_result.scalars().all():
                feeds.append(
                    {
                        "feed_url": row.feed_url,
                        "title": row.title,
                        "author": row.author,
                        "description": row.description,
                        "website": row.website,
                        "logo_url": row.logo_url,
                        "mygpo_link": row.mygpo_link,
                        "categories": list(row.categories) if row.categories else None,
                        "created_at": _as_iso(row.created_at),
                        "updated_at": _as_iso(row.updated_at),
                    }
                )

        if episode_urls:
            episode_result = await self.session.execute(
                select(EpisodeModel, PodcastFeedModel.feed_url)
                .join(PodcastFeedModel, EpisodeModel.feed_id == PodcastFeedModel.id)
                .where(EpisodeModel.episode_url.in_(episode_urls))
            )
            for row, feed_url in episode_result.all():
                episodes.append(
                    {
                        "feed_url": feed_url,
                        "episode_url": row.episode_url,
                        "title": row.title,
                        "description": row.description,
                        "website": row.website,
                        "mygpo_link": row.mygpo_link,
                        "released_at": _as_iso(row.released_at),
                        "created_at": _as_iso(row.created_at),
                        "updated_at": _as_iso(row.updated_at),
                    }
                )

        return feeds, episodes

    async def _import_podcast_feeds(self, snapshot: UserDataSnapshot) -> None:
        if not snapshot.podcast_feeds:
            return
        urls = [row.feed_url for row in snapshot.podcast_feeds]
        result = await self.session.execute(
            select(PodcastFeedModel).where(PodcastFeedModel.feed_url.in_(urls))
        )
        existing_map = {row.feed_url: row for row in result.scalars().all()}
        for row in snapshot.podcast_feeds:
            existing = existing_map.get(row.feed_url)
            if existing is None:
                self.session.add(
                    PodcastFeedModel(
                        feed_url=row.feed_url,
                        title=row.title,
                        author=row.author,
                        description=row.description,
                        website=row.website,
                        logo_url=row.logo_url,
                        mygpo_link=row.mygpo_link,
                        categories=row.categories,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.title = row.title
            existing.author = row.author
            existing.description = row.description
            existing.website = row.website
            existing.logo_url = row.logo_url
            existing.mygpo_link = row.mygpo_link
            existing.categories = row.categories
            existing.updated_at = row.updated_at

    async def _import_episodes(
        self, snapshot: UserDataSnapshot, feed_id_map: dict[str, int]
    ) -> None:
        if not snapshot.episodes:
            return
        urls = [row.episode_url for row in snapshot.episodes]
        result = await self.session.execute(
            select(EpisodeModel).where(EpisodeModel.episode_url.in_(urls))
        )
        existing_map = {row.episode_url: row for row in result.scalars().all()}
        for row in snapshot.episodes:
            feed_id = feed_id_map.get(row.feed_url)
            if feed_id is None:
                continue
            existing = existing_map.get(row.episode_url)
            if existing is None:
                self.session.add(
                    EpisodeModel(
                        feed_id=feed_id,
                        episode_url=row.episode_url,
                        title=row.title,
                        description=row.description,
                        website=row.website,
                        mygpo_link=row.mygpo_link,
                        released_at=row.released_at,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.feed_id = feed_id
            existing.title = row.title
            existing.description = row.description
            existing.website = row.website
            existing.mygpo_link = row.mygpo_link
            existing.released_at = row.released_at
            existing.updated_at = row.updated_at

    async def _import_devices(
        self, user: UserModel, snapshot: UserDataSnapshot
    ) -> None:
        existing_result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.user_id == user.id)
        )
        existing_by_device_id = {
            row.device_id: row for row in existing_result.scalars().all()
        }

        for row in snapshot.devices:
            existing = existing_by_device_id.get(row.device_id)
            if existing is None:
                model = DeviceModel(
                    user_id=user.id,
                    device_id=row.device_id,
                    caption=row.caption,
                    device_type=row.device_type,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                self.session.add(model)
                existing_by_device_id[row.device_id] = model
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.caption = row.caption
            existing.device_type = row.device_type
            existing.updated_at = row.updated_at

    async def _rebuild_device_sync_groups(
        self, user: UserModel, snapshot: UserDataSnapshot
    ) -> None:
        if not snapshot.devices:
            return

        await self.session.execute(
            delete(DeviceSyncGroupModel).where(DeviceSyncGroupModel.user_id == user.id)
        )
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.user_id == user.id)
        )
        devices_by_device_id = {row.device_id: row for row in result.scalars().all()}
        for device in devices_by_device_id.values():
            device.sync_group_id = None

        devices_for_group: dict[str, list[DeviceModel]] = {}
        for device_row in snapshot.devices:
            if device_row.sync_group is None:
                continue
            model = devices_by_device_id.get(device_row.device_id)
            if model is None:
                continue
            devices_for_group.setdefault(device_row.sync_group, []).append(model)

        now = datetime.now(UTC)
        for members in devices_for_group.values():
            if len(members) < 2:
                continue
            group_model = DeviceSyncGroupModel(
                user_id=user.id, created_at=now, updated_at=now
            )
            self.session.add(group_model)
            await self.session.flush()
            for member in members:
                member.sync_group_id = group_model.id

    async def _import_account_settings(
        self, user: UserModel, snapshot: UserDataSnapshot
    ) -> None:
        if not snapshot.account_settings:
            return
        row = snapshot.account_settings[0]
        result = await self.session.execute(
            select(AccountSettingModel).where(AccountSettingModel.user_id == user.id)
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            self.session.add(
                AccountSettingModel(
                    user_id=user.id,
                    settings=row.settings,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
            )
            return
        if _as_utc(existing.updated_at) >= row.updated_at:
            return
        existing.settings = row.settings
        existing.updated_at = row.updated_at

    async def _import_device_settings(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        device_pk_map: dict[str, int],
    ) -> None:
        if not snapshot.device_settings:
            return
        device_pks = list(device_pk_map.values())
        if not device_pks:
            return
        result = await self.session.execute(
            select(DeviceSettingModel).where(
                DeviceSettingModel.user_id == user.id,
                DeviceSettingModel.device_pk.in_(device_pks),
            )
        )
        existing_map = {row.device_pk: row for row in result.scalars().all()}
        for row in snapshot.device_settings:
            device_pk = device_pk_map.get(row.device_id)
            if device_pk is None:
                continue
            existing = existing_map.get(device_pk)
            if existing is None:
                self.session.add(
                    DeviceSettingModel(
                        user_id=user.id,
                        device_pk=device_pk,
                        settings=row.settings,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.settings = row.settings
            existing.updated_at = row.updated_at

    async def _import_podcast_settings(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        feed_id_map: dict[str, int],
    ) -> None:
        if not snapshot.podcast_settings:
            return
        feed_ids = list(feed_id_map.values())
        if not feed_ids:
            return
        result = await self.session.execute(
            select(PodcastSettingModel).where(
                PodcastSettingModel.user_id == user.id,
                PodcastSettingModel.feed_id.in_(feed_ids),
            )
        )
        existing_map = {row.feed_id: row for row in result.scalars().all()}
        for row in snapshot.podcast_settings:
            feed_id = feed_id_map.get(row.feed_url)
            if feed_id is None:
                continue
            existing = existing_map.get(feed_id)
            if existing is None:
                self.session.add(
                    PodcastSettingModel(
                        user_id=user.id,
                        feed_id=feed_id,
                        settings=row.settings,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.settings = row.settings
            existing.updated_at = row.updated_at

    async def _import_episode_settings(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        episode_id_map: dict[str, int],
    ) -> None:
        if not snapshot.episode_settings:
            return
        episode_ids = list(episode_id_map.values())
        if not episode_ids:
            return
        result = await self.session.execute(
            select(EpisodeSettingModel).where(
                EpisodeSettingModel.user_id == user.id,
                EpisodeSettingModel.episode_id.in_(episode_ids),
            )
        )
        existing_map = {row.episode_id: row for row in result.scalars().all()}
        for row in snapshot.episode_settings:
            episode_id = episode_id_map.get(row.episode_url)
            if episode_id is None:
                continue
            existing = existing_map.get(episode_id)
            if existing is None:
                self.session.add(
                    EpisodeSettingModel(
                        user_id=user.id,
                        episode_id=episode_id,
                        settings=row.settings,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.settings = row.settings
            existing.updated_at = row.updated_at

    async def _import_podcast_lists(
        self, user: UserModel, snapshot: UserDataSnapshot
    ) -> None:
        existing_result = await self.session.execute(
            select(PodcastListModel).where(PodcastListModel.user_id == user.id)
        )
        existing_by_name = {row.name: row for row in existing_result.scalars().all()}
        for row in snapshot.podcast_lists:
            existing = existing_by_name.get(row.name)
            if existing is None:
                model = PodcastListModel(
                    user_id=user.id,
                    title=row.title,
                    name=row.name,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                self.session.add(model)
                existing_by_name[row.name] = model
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.title = row.title
            existing.updated_at = row.updated_at

    async def _import_podcast_list_items(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        feed_id_map: dict[str, int],
        list_id_map: dict[str, int],
    ) -> None:
        if not snapshot.podcast_list_items:
            return
        list_ids = list(list_id_map.values())
        if not list_ids:
            return
        result = await self.session.execute(
            select(PodcastListItemModel).where(
                PodcastListItemModel.list_id.in_(list_ids),
            )
        )
        existing_map = {
            (row.list_id, row.feed_id): row for row in result.scalars().all()
        }
        for row in snapshot.podcast_list_items:
            list_id = list_id_map.get(row.list_name)
            feed_id = feed_id_map.get(row.feed_url)
            if list_id is None or feed_id is None:
                continue
            existing = existing_map.get((list_id, feed_id))
            if existing is None:
                self.session.add(
                    PodcastListItemModel(
                        list_id=list_id,
                        feed_id=feed_id,
                        position=row.position,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.position = row.position
            existing.updated_at = row.updated_at

    async def _import_device_subscriptions(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        device_pk_map: dict[str, int],
        feed_id_map: dict[str, int],
    ) -> None:
        if not snapshot.device_subscriptions:
            return
        device_pks = list(device_pk_map.values())
        if not device_pks:
            return
        result = await self.session.execute(
            select(DeviceSubscriptionModel).where(
                DeviceSubscriptionModel.device_pk.in_(device_pks),
            )
        )
        existing_map = {
            (row.device_pk, row.feed_id): row for row in result.scalars().all()
        }
        for row in snapshot.device_subscriptions:
            device_pk = device_pk_map.get(row.device_id)
            feed_id = feed_id_map.get(row.feed_url)
            if device_pk is None or feed_id is None:
                continue
            existing = existing_map.get((device_pk, feed_id))
            if existing is None:
                self.session.add(
                    DeviceSubscriptionModel(
                        device_pk=device_pk,
                        feed_id=feed_id,
                        subscribed_at=row.subscribed_at,
                        unsubscribed_at=row.unsubscribed_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.subscribed_at = row.subscribed_at
            existing.unsubscribed_at = row.unsubscribed_at
            existing.updated_at = row.updated_at

    async def _import_episode_actions(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        device_pk_map: dict[str, int],
        episode_id_map: dict[str, int],
    ) -> None:
        if not snapshot.episode_actions:
            return
        episode_ids = list(episode_id_map.values())
        if not episode_ids:
            return
        result = await self.session.execute(
            select(EpisodeActionModel).where(
                EpisodeActionModel.user_id == user.id,
                EpisodeActionModel.episode_id.in_(episode_ids),
            )
        )
        existing_map = {row.episode_id: row for row in result.scalars().all()}
        for row in snapshot.episode_actions:
            episode_id = episode_id_map.get(row.episode_url)
            if episode_id is None:
                continue
            device_pk = device_pk_map.get(row.device_id) if row.device_id else None
            existing = existing_map.get(episode_id)
            if existing is None:
                self.session.add(
                    EpisodeActionModel(
                        user_id=user.id,
                        device_pk=device_pk,
                        episode_id=episode_id,
                        status=row.status,
                        action=row.action,
                        occurred_at=row.occurred_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.occurred_at) >= row.occurred_at:
                continue
            existing.device_pk = device_pk
            existing.status = row.status
            existing.action = row.action
            existing.occurred_at = row.occurred_at
            existing.updated_at = row.updated_at

    async def _import_favorite_episodes(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        episode_id_map: dict[str, int],
    ) -> None:
        if not snapshot.favorite_episodes:
            return
        episode_ids = list(episode_id_map.values())
        if not episode_ids:
            return
        result = await self.session.execute(
            select(FavoriteEpisodeModel).where(
                FavoriteEpisodeModel.user_id == user.id,
                FavoriteEpisodeModel.episode_id.in_(episode_ids),
            )
        )
        existing_map = {row.episode_id: row for row in result.scalars().all()}
        for row in snapshot.favorite_episodes:
            episode_id = episode_id_map.get(row.episode_url)
            if episode_id is None:
                continue
            existing = existing_map.get(episode_id)
            if existing is None:
                self.session.add(
                    FavoriteEpisodeModel(
                        user_id=user.id,
                        episode_id=episode_id,
                        favorited_at=row.favorited_at,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                    )
                )
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.favorited_at = row.favorited_at
            existing.updated_at = row.updated_at

    async def _import_subscription_change_events(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        device_pk_map: dict[str, int],
    ) -> None:
        if not snapshot.subscription_change_events:
            return
        device_pks = list(device_pk_map.values())
        if not device_pks:
            return
        result = await self.session.execute(
            select(
                SubscriptionChangeEventModel.device_pk,
                SubscriptionChangeEventModel.feed_url,
                SubscriptionChangeEventModel.operation,
                SubscriptionChangeEventModel.created_at,
            ).where(SubscriptionChangeEventModel.device_pk.in_(device_pks))
        )
        existing_keys = {
            (device_pk, feed_url, operation, _as_utc(created_at))
            for device_pk, feed_url, operation, created_at in result.all()
        }
        for row in snapshot.subscription_change_events:
            device_pk = device_pk_map.get(row.device_id)
            if device_pk is None:
                continue
            key = (device_pk, row.feed_url, row.operation, row.created_at)
            if key in existing_keys:
                continue
            self.session.add(
                SubscriptionChangeEventModel(
                    device_pk=device_pk,
                    feed_url=row.feed_url,
                    operation=row.operation,
                    created_at=row.created_at,
                )
            )

    async def _import_episode_action_events(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        episode_id_map: dict[str, int],
    ) -> None:
        if not snapshot.episode_action_events:
            return
        episode_urls = {row.episode_url for row in snapshot.episode_action_events}
        result = await self.session.execute(
            select(
                EpisodeActionEventModel.episode_url,
                EpisodeActionEventModel.action,
                EpisodeActionEventModel.occurred_at,
            ).where(
                EpisodeActionEventModel.user_id == user.id,
                EpisodeActionEventModel.episode_url.in_(episode_urls),
            )
        )
        existing_keys = {
            (ep_url, action, _as_utc(occurred_at))
            for ep_url, action, occurred_at in result.all()
        }
        for row in snapshot.episode_action_events:
            key = (row.episode_url, row.action, row.occurred_at)
            if key in existing_keys:
                continue
            episode_id = episode_id_map.get(row.episode_url)
            if episode_id is None:
                continue
            self.session.add(
                EpisodeActionEventModel(
                    user_id=user.id,
                    episode_id=episode_id,
                    podcast_url=row.podcast_url,
                    episode_url=row.episode_url,
                    device_id=row.device_id,
                    action=row.action,
                    occurred_at=row.occurred_at,
                    started=row.started,
                    position=row.position,
                    total=row.total,
                    created_at=row.created_at,
                )
            )

    async def _export_episode_playlists(self, user: UserModel) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(EpisodePlaylistModel).where(EpisodePlaylistModel.user_id == user.id)
        )
        return [
            {
                "title": row.title,
                "description": row.description,
                "image_url": row.image_url,
                "created_at": _as_iso(row.created_at),
                "updated_at": _as_iso(row.updated_at),
            }
            for row in result.scalars().all()
        ]

    async def _export_episode_playlist_items(
        self, user: UserModel
    ) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(
                EpisodePlaylistItemModel,
                EpisodePlaylistModel.title,
                EpisodeModel.episode_url,
            )
            .join(
                EpisodePlaylistModel,
                EpisodePlaylistItemModel.playlist_id == EpisodePlaylistModel.id,
            )
            .join(EpisodeModel, EpisodePlaylistItemModel.episode_id == EpisodeModel.id)
            .where(EpisodePlaylistModel.user_id == user.id)
        )
        return [
            {
                "playlist_title": playlist_title,
                "episode_url": episode_url,
                "created_at": _as_iso(item.created_at),
            }
            for item, playlist_title, episode_url in result.all()
        ]

    async def _import_episode_playlists(
        self, user: UserModel, snapshot: UserDataSnapshot
    ) -> None:
        if not snapshot.episode_playlists:
            return
        existing_result = await self.session.execute(
            select(EpisodePlaylistModel).where(EpisodePlaylistModel.user_id == user.id)
        )
        existing_by_title = {row.title: row for row in existing_result.scalars().all()}
        for row in snapshot.episode_playlists:
            existing = existing_by_title.get(row.title)
            if existing is None:
                model = EpisodePlaylistModel(
                    user_id=user.id,
                    title=row.title,
                    description=row.description,
                    image_url=row.image_url,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                self.session.add(model)
                existing_by_title[row.title] = model
                continue
            if _as_utc(existing.updated_at) >= row.updated_at:
                continue
            existing.description = row.description
            existing.image_url = row.image_url
            existing.updated_at = row.updated_at

    async def _import_episode_playlist_items(
        self,
        user: UserModel,
        snapshot: UserDataSnapshot,
        episode_id_map: dict[str, int],
    ) -> None:
        if not snapshot.episode_playlist_items:
            return
        playlist_result = await self.session.execute(
            select(EpisodePlaylistModel.title, EpisodePlaylistModel.id).where(
                EpisodePlaylistModel.user_id == user.id
            )
        )
        playlist_id_map: dict[str, int] = {
            title: int(pid) for title, pid in playlist_result.all()
        }
        playlist_ids = list(playlist_id_map.values())
        if not playlist_ids:
            return

        existing_result = await self.session.execute(
            select(
                EpisodePlaylistItemModel.playlist_id,
                EpisodePlaylistItemModel.episode_id,
            ).where(EpisodePlaylistItemModel.playlist_id.in_(playlist_ids))
        )
        existing_pairs = {(int(r[0]), int(r[1])) for r in existing_result.all()}

        now = datetime.now(UTC)
        for row in snapshot.episode_playlist_items:
            playlist_id = playlist_id_map.get(row.playlist_title)
            episode_id = episode_id_map.get(row.episode_url)
            if playlist_id is None or episode_id is None:
                continue
            if (playlist_id, episode_id) in existing_pairs:
                continue
            self.session.add(
                EpisodePlaylistItemModel(
                    playlist_id=playlist_id,
                    episode_id=episode_id,
                    created_at=row.created_at,
                    updated_at=now,
                )
            )

    async def _feed_id_map(self, feed_urls: set[str]) -> dict[str, int]:
        if not feed_urls:
            return {}
        result = await self.session.execute(
            select(PodcastFeedModel.id, PodcastFeedModel.feed_url).where(
                PodcastFeedModel.feed_url.in_(feed_urls)
            )
        )
        return {feed_url: feed_id for feed_id, feed_url in result.all()}

    async def _episode_id_map(self, episode_urls: set[str]) -> dict[str, int]:
        if not episode_urls:
            return {}
        result = await self.session.execute(
            select(EpisodeModel.id, EpisodeModel.episode_url).where(
                EpisodeModel.episode_url.in_(episode_urls)
            )
        )
        return {episode_url: episode_id for episode_id, episode_url in result.all()}

    async def _device_pk_map(self, user_id: int) -> dict[str, int]:
        result = await self.session.execute(
            select(DeviceModel.id, DeviceModel.device_id).where(
                DeviceModel.user_id == user_id
            )
        )
        return {device_id: device_pk for device_pk, device_id in result.all()}

    async def _list_id_map(self, user_id: int) -> dict[str, int]:
        result = await self.session.execute(
            select(PodcastListModel.id, PodcastListModel.name).where(
                PodcastListModel.user_id == user_id
            )
        )
        return {name: list_id for list_id, name in result.all()}
