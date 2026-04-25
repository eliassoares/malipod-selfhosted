from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from app.db.models.device import DeviceModel
from app.db.models.podcast import (
    DeviceSubscriptionModel,
    EpisodeActionEventModel,
    EpisodeActionModel,
    EpisodeModel,
    EpisodePlaylistItemModel,
    EpisodePlaylistModel,
    PodcastFeedModel,
    SubscriptionChangeEventModel,
)
from app.db.models.session import AuthenticatedSessionModel
from app.schemas.auth import RegistrationInput
from app.schemas.user_data_tools import UserDataSnapshot
from app.services.auth import AuthService
from app.services.user_data_tools import UserDataToolsService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings
    from app.db.models.user import UserModel


def _user_row(user: UserModel) -> dict[str, object]:
    return {
        "nickname": user.nickname,
        "email": user.email,
        "picture_url": user.picture_url,
        "language_preference": user.language_preference,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "accessed_at": user.accessed_at.isoformat(),
        "deactivated_at": None,
    }


def build_registration(
    nickname: str = "listener_1", email: str = "listener@example.com"
) -> RegistrationInput:
    return RegistrationInput(
        nickname=nickname,
        email=email,
        password="supersecret",
        password_confirmation="supersecret",
        picture_url="https://example.com/avatar.png",
        language_preference="en",
    )


async def create_user(
    db_session: AsyncSession,
    settings: Settings,
    nickname: str = "listener_1",
    email: str = "listener@example.com",
) -> UserModel:
    auth_service = AuthService(db_session, settings)
    return await auth_service.create_user(build_registration(nickname, email))


@pytest.mark.asyncio
async def test_export_snapshot_excludes_password_hash_salt_and_sessions(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    session = AuthenticatedSessionModel(
        session_id="session-1",
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    db_session.add(session)
    await db_session.commit()

    service = UserDataToolsService(db_session)
    snapshot = await service.export_snapshot(user)

    assert "authenticated_sessions" not in snapshot
    assert snapshot["users"][0]["email"] == user.email
    assert "password_hash" not in snapshot["users"][0]
    assert "password_salt" not in snapshot["users"][0]


@pytest.mark.asyncio
async def test_import_snapshot_merges_global_feed_by_updated_at(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)
    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Original",
        author=None,
        description=None,
        website=None,
        logo_url=None,
        mygpo_link=None,
        categories=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.commit()

    service = UserDataToolsService(db_session)

    older_snapshot = UserDataSnapshot.model_validate(
        {
            "users": [
                {
                    "nickname": user.nickname,
                    "email": user.email,
                    "picture_url": user.picture_url,
                    "language_preference": user.language_preference,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "accessed_at": user.accessed_at.isoformat(),
                    "deactivated_at": None,
                }
            ],
            "podcast_feeds": [
                {
                    "feed_url": feed.feed_url,
                    "title": "Older title",
                    "author": None,
                    "description": None,
                    "website": None,
                    "logo_url": None,
                    "mygpo_link": None,
                    "categories": None,
                    "created_at": now.isoformat(),
                    "updated_at": (now - timedelta(days=1)).isoformat(),
                }
            ],
        }
    )
    await service.import_snapshot(user, older_snapshot)
    await db_session.refresh(feed)
    assert feed.title == "Original"

    newer_snapshot = UserDataSnapshot.model_validate(
        {
            "users": older_snapshot.model_dump()["users"],
            "podcast_feeds": [
                {
                    "feed_url": feed.feed_url,
                    "title": "Newer title",
                    "author": None,
                    "description": None,
                    "website": None,
                    "logo_url": None,
                    "mygpo_link": None,
                    "categories": None,
                    "created_at": now.isoformat(),
                    "updated_at": (now + timedelta(days=1)).isoformat(),
                }
            ],
        }
    )
    await service.import_snapshot(user, newer_snapshot)
    await db_session.refresh(feed)
    assert feed.title == "Newer title"


@pytest.mark.asyncio
async def test_import_append_only_subscription_change_events_inserts_if_missing(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)
    device = DeviceModel(
        user_id=user.id,
        device_id="phone-01",
        caption="Phone",
        device_type="mobile",
        created_at=now,
        updated_at=now,
    )
    db_session.add(device)
    await db_session.flush()
    existing = SubscriptionChangeEventModel(
        device_pk=device.id,
        feed_url="https://example.com/feed.xml",
        operation="ADD",
        created_at=now,
    )
    db_session.add(existing)
    await db_session.commit()

    service = UserDataToolsService(db_session)
    snapshot = UserDataSnapshot.model_validate(
        {
            "users": [
                {
                    "nickname": user.nickname,
                    "email": user.email,
                    "picture_url": user.picture_url,
                    "language_preference": user.language_preference,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "accessed_at": user.accessed_at.isoformat(),
                    "deactivated_at": None,
                }
            ],
            "devices": [
                {
                    "device_id": "phone-01",
                    "caption": "Phone",
                    "device_type": "mobile",
                    "sync_group": None,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "subscription_change_events": [
                {
                    "device_id": "phone-01",
                    "feed_url": "https://example.com/feed.xml",
                    "operation": "ADD",
                    "created_at": now.isoformat(),
                },
                {
                    "device_id": "phone-01",
                    "feed_url": "https://example.com/feed-2.xml",
                    "operation": "ADD",
                    "created_at": (now + timedelta(seconds=10)).isoformat(),
                },
            ],
        }
    )
    await service.import_snapshot(user, snapshot)

    rows = (
        (
            await db_session.execute(
                select(SubscriptionChangeEventModel).where(
                    SubscriptionChangeEventModel.device_pk == device.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_import_devices_skips_older_and_applies_newer(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)
    device = DeviceModel(
        user_id=user.id,
        device_id="phone-01",
        caption="Original",
        device_type="mobile",
        created_at=now,
        updated_at=now,
    )
    db_session.add(device)
    await db_session.commit()

    def make_snapshot(caption: str, updated_at: datetime) -> UserDataSnapshot:
        return UserDataSnapshot.model_validate(
            {
                "users": [_user_row(user)],
                "devices": [
                    {
                        "device_id": "phone-01",
                        "caption": caption,
                        "device_type": "mobile",
                        "sync_group": None,
                        "created_at": now.isoformat(),
                        "updated_at": updated_at.isoformat(),
                    }
                ],
            }
        )

    service = UserDataToolsService(db_session)

    await service.import_snapshot(
        user, make_snapshot("Old caption", now - timedelta(seconds=1))
    )
    await db_session.refresh(device)
    assert device.caption == "Original"

    await service.import_snapshot(
        user, make_snapshot("New caption", now + timedelta(seconds=1))
    )
    await db_session.refresh(device)
    assert device.caption == "New caption"


@pytest.mark.asyncio
async def test_import_episode_actions_uses_occurred_at_as_tiebreaker(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Test Feed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.flush()

    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep1.mp3",
        title="Episode 1",
        released_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.flush()

    action = EpisodeActionModel(
        user_id=user.id,
        episode_id=episode.id,
        status="play",
        action=None,
        occurred_at=now,
        updated_at=now,
    )
    db_session.add(action)
    await db_session.commit()

    def make_snapshot(status: str, occurred_at: datetime) -> UserDataSnapshot:
        return UserDataSnapshot.model_validate(
            {
                "users": [_user_row(user)],
                "podcast_feeds": [
                    {
                        "feed_url": "https://example.com/feed.xml",
                        "title": "Test Feed",
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                    }
                ],
                "episodes": [
                    {
                        "feed_url": "https://example.com/feed.xml",
                        "episode_url": "https://example.com/ep1.mp3",
                        "title": "Episode 1",
                        "released_at": now.isoformat(),
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                    }
                ],
                "episode_actions": [
                    {
                        "episode_url": "https://example.com/ep1.mp3",
                        "status": status,
                        "action": None,
                        "device_id": None,
                        "occurred_at": occurred_at.isoformat(),
                        "updated_at": occurred_at.isoformat(),
                    }
                ],
            }
        )

    service = UserDataToolsService(db_session)

    await service.import_snapshot(
        user, make_snapshot("delete", now - timedelta(seconds=1))
    )
    await db_session.refresh(action)
    assert action.status == "play"

    await service.import_snapshot(
        user, make_snapshot("delete", now + timedelta(seconds=1))
    )
    await db_session.refresh(action)
    assert action.status == "delete"


@pytest.mark.asyncio
async def test_import_episode_action_events_is_append_only(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Test Feed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.flush()

    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep1.mp3",
        title="Episode 1",
        released_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.flush()

    existing_event = EpisodeActionEventModel(
        user_id=user.id,
        episode_id=episode.id,
        podcast_url="https://example.com/feed.xml",
        episode_url="https://example.com/ep1.mp3",
        device_id=None,
        action="play",
        occurred_at=now,
        created_at=now,
    )
    db_session.add(existing_event)
    await db_session.commit()

    snapshot = UserDataSnapshot.model_validate(
        {
            "users": [_user_row(user)],
            "podcast_feeds": [
                {
                    "feed_url": "https://example.com/feed.xml",
                    "title": "Test Feed",
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "episodes": [
                {
                    "feed_url": "https://example.com/feed.xml",
                    "episode_url": "https://example.com/ep1.mp3",
                    "title": "Episode 1",
                    "released_at": now.isoformat(),
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "episode_action_events": [
                {
                    "episode_url": "https://example.com/ep1.mp3",
                    "podcast_url": "https://example.com/feed.xml",
                    "action": "play",
                    "occurred_at": now.isoformat(),
                    "created_at": now.isoformat(),
                },
                {
                    "episode_url": "https://example.com/ep1.mp3",
                    "podcast_url": "https://example.com/feed.xml",
                    "action": "play",
                    "occurred_at": (now + timedelta(seconds=10)).isoformat(),
                    "created_at": (now + timedelta(seconds=10)).isoformat(),
                },
            ],
        }
    )

    service = UserDataToolsService(db_session)
    await service.import_snapshot(user, snapshot)

    result = await db_session.execute(
        select(EpisodeActionEventModel).where(
            EpisodeActionEventModel.user_id == user.id
        )
    )
    events = result.scalars().all()
    assert len(events) == 2


@pytest.mark.asyncio
async def test_import_podcast_feed_missing_in_db_is_inserted(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    service = UserDataToolsService(db_session)
    snapshot = UserDataSnapshot.model_validate(
        {
            "users": [_user_row(user)],
            "podcast_feeds": [
                {
                    "feed_url": "https://example.com/missing-feed.xml",
                    "title": "Missing Feed",
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
        }
    )
    await service.import_snapshot(user, snapshot)

    result = await db_session.execute(
        select(PodcastFeedModel).where(
            PodcastFeedModel.feed_url == "https://example.com/missing-feed.xml"
        )
    )
    feed = result.scalar_one_or_none()
    assert feed is not None
    assert feed.title == "Missing Feed"


@pytest.mark.asyncio
async def test_import_episodes_skips_older_and_applies_newer(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Feed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.flush()

    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep1.mp3",
        title="Original title",
        released_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.commit()

    def make_snapshot(title: str, updated_at: datetime) -> UserDataSnapshot:
        return UserDataSnapshot.model_validate(
            {
                "users": [_user_row(user)],
                "podcast_feeds": [
                    {
                        "feed_url": "https://example.com/feed.xml",
                        "title": "Feed",
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                    }
                ],
                "episodes": [
                    {
                        "feed_url": "https://example.com/feed.xml",
                        "episode_url": "https://example.com/ep1.mp3",
                        "title": title,
                        "released_at": now.isoformat(),
                        "created_at": now.isoformat(),
                        "updated_at": updated_at.isoformat(),
                    }
                ],
            }
        )

    service = UserDataToolsService(db_session)

    await service.import_snapshot(
        user, make_snapshot("Older title", now - timedelta(seconds=1))
    )
    await db_session.refresh(episode)
    assert episode.title == "Original title"

    await service.import_snapshot(
        user, make_snapshot("Newer title", now + timedelta(seconds=1))
    )
    await db_session.refresh(episode)
    assert episode.title == "Newer title"


@pytest.mark.asyncio
async def test_import_episode_missing_in_db_is_inserted(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Feed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.commit()

    service = UserDataToolsService(db_session)
    snapshot = UserDataSnapshot.model_validate(
        {
            "users": [_user_row(user)],
            "podcast_feeds": [
                {
                    "feed_url": "https://example.com/feed.xml",
                    "title": "Feed",
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "episodes": [
                {
                    "feed_url": "https://example.com/feed.xml",
                    "episode_url": "https://example.com/missing-ep.mp3",
                    "title": "Missing Episode",
                    "released_at": now.isoformat(),
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
        }
    )
    await service.import_snapshot(user, snapshot)

    result = await db_session.execute(
        select(EpisodeModel).where(
            EpisodeModel.episode_url == "https://example.com/missing-ep.mp3"
        )
    )
    episode = result.scalar_one_or_none()
    assert episode is not None
    assert episode.title == "Missing Episode"


@pytest.mark.asyncio
async def test_import_device_subscriptions_skips_older_and_applies_newer(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    device = DeviceModel(
        user_id=user.id,
        device_id="phone-01",
        caption="Phone",
        device_type="mobile",
        created_at=now,
        updated_at=now,
    )
    db_session.add(device)
    await db_session.flush()

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Feed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.flush()

    sub = DeviceSubscriptionModel(
        device_pk=device.id,
        feed_id=feed.id,
        subscribed_at=now,
        unsubscribed_at=None,
        updated_at=now,
    )
    db_session.add(sub)
    await db_session.commit()

    def make_snapshot(
        unsubscribed_at: datetime | None, updated_at: datetime
    ) -> UserDataSnapshot:
        return UserDataSnapshot.model_validate(
            {
                "users": [_user_row(user)],
                "devices": [
                    {
                        "device_id": "phone-01",
                        "caption": "Phone",
                        "device_type": "mobile",
                        "sync_group": None,
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                    }
                ],
                "podcast_feeds": [
                    {
                        "feed_url": "https://example.com/feed.xml",
                        "title": "Feed",
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                    }
                ],
                "device_subscriptions": [
                    {
                        "device_id": "phone-01",
                        "feed_url": "https://example.com/feed.xml",
                        "subscribed_at": now.isoformat(),
                        "unsubscribed_at": (
                            unsubscribed_at.isoformat() if unsubscribed_at else None
                        ),
                        "updated_at": updated_at.isoformat(),
                    }
                ],
            }
        )

    service = UserDataToolsService(db_session)

    await service.import_snapshot(
        user, make_snapshot(now - timedelta(seconds=1), now - timedelta(seconds=1))
    )
    await db_session.refresh(sub)
    assert sub.unsubscribed_at is None

    await service.import_snapshot(
        user, make_snapshot(now + timedelta(seconds=1), now + timedelta(seconds=1))
    )
    await db_session.refresh(sub)
    assert sub.unsubscribed_at is not None


@pytest.mark.asyncio
async def test_import_device_subscription_missing_in_db_is_inserted(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    device = DeviceModel(
        user_id=user.id,
        device_id="phone-01",
        caption="Phone",
        device_type="mobile",
        created_at=now,
        updated_at=now,
    )
    db_session.add(device)
    await db_session.flush()

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Feed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.commit()

    service = UserDataToolsService(db_session)
    snapshot = UserDataSnapshot.model_validate(
        {
            "users": [_user_row(user)],
            "devices": [
                {
                    "device_id": "phone-01",
                    "caption": "Phone",
                    "device_type": "mobile",
                    "sync_group": None,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "podcast_feeds": [
                {
                    "feed_url": "https://example.com/feed.xml",
                    "title": "Feed",
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "device_subscriptions": [
                {
                    "device_id": "phone-01",
                    "feed_url": "https://example.com/feed.xml",
                    "subscribed_at": now.isoformat(),
                    "unsubscribed_at": None,
                    "updated_at": now.isoformat(),
                }
            ],
        }
    )
    await service.import_snapshot(user, snapshot)

    result = await db_session.execute(
        select(DeviceSubscriptionModel).where(
            DeviceSubscriptionModel.device_pk == device.id,
            DeviceSubscriptionModel.feed_id == feed.id,
        )
    )
    sub = result.scalar_one_or_none()
    assert sub is not None
    assert sub.unsubscribed_at is None


@pytest.mark.asyncio
async def test_export_includes_episode_playlists(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Feed",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.flush()

    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep1",
        title="Ep 1",
        released_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.flush()

    playlist = EpisodePlaylistModel(
        user_id=user.id,
        title="My List",
        description="desc",
        image_url=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(playlist)
    await db_session.flush()

    item = EpisodePlaylistItemModel(
        playlist_id=playlist.id,
        episode_id=episode.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(item)
    await db_session.commit()

    service = UserDataToolsService(db_session)
    snapshot = await service.export_snapshot(user)

    assert len(snapshot["episode_playlists"]) == 1
    assert snapshot["episode_playlists"][0]["title"] == "My List"
    assert len(snapshot["episode_playlist_items"]) == 1
    assert snapshot["episode_playlist_items"][0]["playlist_title"] == "My List"
    item = snapshot["episode_playlist_items"][0]
    assert item["episode_url"] == str(episode.episode_url)


@pytest.mark.asyncio
async def test_import_episode_playlists_round_trip(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed2.xml",
        title="Feed2",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.flush()

    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep2",
        title="Ep 2",
        released_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.commit()

    service = UserDataToolsService(db_session)
    snapshot = UserDataSnapshot.model_validate(
        {
            "users": [
                {
                    "nickname": user.nickname,
                    "email": user.email,
                    "picture_url": user.picture_url,
                    "language_preference": user.language_preference,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "accessed_at": user.accessed_at.isoformat(),
                    "deactivated_at": None,
                }
            ],
            "podcast_feeds": [
                {
                    "feed_url": "https://example.com/feed2.xml",
                    "title": "Feed2",
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "episodes": [
                {
                    "feed_url": "https://example.com/feed2.xml",
                    "episode_url": "https://example.com/ep2",
                    "title": "Ep 2",
                    "released_at": now.isoformat(),
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "episode_playlists": [
                {
                    "title": "Imported Playlist",
                    "description": "imported",
                    "image_url": None,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            ],
            "episode_playlist_items": [
                {
                    "playlist_title": "Imported Playlist",
                    "episode_url": "https://example.com/ep2",
                    "created_at": now.isoformat(),
                }
            ],
        }
    )
    await service.import_snapshot(user, snapshot)

    playlists = (
        (
            await db_session.execute(
                select(EpisodePlaylistModel).where(
                    EpisodePlaylistModel.user_id == user.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(playlists) == 1
    assert playlists[0].title == "Imported Playlist"

    items = (
        (
            await db_session.execute(
                select(EpisodePlaylistItemModel).where(
                    EpisodePlaylistItemModel.playlist_id == playlists[0].id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(items) == 1


@pytest.mark.asyncio
async def test_import_episode_playlists_is_idempotent(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)

    feed = PodcastFeedModel(
        feed_url="https://example.com/feed3.xml",
        title="Feed3",
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.flush()

    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/ep3",
        title="Ep 3",
        released_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.commit()

    base_snapshot = {
        "users": [
            {
                "nickname": user.nickname,
                "email": user.email,
                "picture_url": user.picture_url,
                "language_preference": user.language_preference,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
                "accessed_at": user.accessed_at.isoformat(),
                "deactivated_at": None,
            }
        ],
        "podcast_feeds": [
            {
                "feed_url": "https://example.com/feed3.xml",
                "title": "Feed3",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        ],
        "episodes": [
            {
                "feed_url": "https://example.com/feed3.xml",
                "episode_url": "https://example.com/ep3",
                "title": "Ep 3",
                "released_at": now.isoformat(),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        ],
        "episode_playlists": [
            {
                "title": "Idempotent Playlist",
                "description": None,
                "image_url": None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        ],
        "episode_playlist_items": [
            {
                "playlist_title": "Idempotent Playlist",
                "episode_url": "https://example.com/ep3",
                "created_at": now.isoformat(),
            }
        ],
    }

    service = UserDataToolsService(db_session)
    await service.import_snapshot(user, UserDataSnapshot.model_validate(base_snapshot))
    await service.import_snapshot(user, UserDataSnapshot.model_validate(base_snapshot))

    playlists = (
        (
            await db_session.execute(
                select(EpisodePlaylistModel).where(
                    EpisodePlaylistModel.user_id == user.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(playlists) == 1

    items = (
        (
            await db_session.execute(
                select(EpisodePlaylistItemModel).where(
                    EpisodePlaylistItemModel.playlist_id == playlists[0].id
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(items) == 1
