from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from app.db.models.device import DeviceModel
from app.db.models.podcast import PodcastFeedModel, SubscriptionChangeEventModel
from app.db.models.session import AuthenticatedSessionModel
from app.schemas.auth import RegistrationInput
from app.schemas.user_data_tools import UserDataSnapshot
from app.services.auth import AuthService
from app.services.user_data_tools import UserDataToolsService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings
    from app.db.models.user import UserModel


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
