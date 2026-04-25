from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select

from app.db.models.device import DeviceModel
from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.schemas.auth import RegistrationInput
from app.schemas.web_player import PlayerStateInput
from app.services.auth import AuthService
from app.services.web_player import WEB_PLAYER_DEVICE_ID, WebPlayerService

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


async def create_episode(db_session: AsyncSession) -> EpisodeModel:
    now = datetime.now(UTC)
    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Feed",
        description=None,
        website=None,
        logo_url=None,
        mygpo_link=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(feed)
    await db_session.flush()
    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/episode-1",
        title="Episode 1",
        description=None,
        website=None,
        media_url="https://example.com/audio.mp3",
        mygpo_link=None,
        released_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.commit()
    await db_session.refresh(episode)
    return episode


@pytest.mark.asyncio
async def test_get_or_create_web_device_is_idempotent(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    service = WebPlayerService(session=db_session, settings=settings)

    device1 = await service.get_or_create_web_device(user)
    device2 = await service.get_or_create_web_device(user)

    assert device1.id == device2.id
    assert device1.device_id == WEB_PLAYER_DEVICE_ID

    rows = (
        (
            await db_session.execute(
                select(DeviceModel).where(
                    DeviceModel.user_id == user.id,
                    DeviceModel.device_id == WEB_PLAYER_DEVICE_ID,
                ),
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_upsert_state_persists_last_state(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    episode = await create_episode(db_session)
    service = WebPlayerService(session=db_session, settings=settings)

    await service.upsert_state(
        user,
        PlayerStateInput(
            episode_id=episode.id,
            position_sec=99,
            queue_mode="podcast",
            queue_ref_id=episode.feed_id,
        ),
    )
    await db_session.refresh(user)

    assert user.last_episode_id == episode.id
    assert user.last_position_sec == 99
    assert user.last_queue_mode == "podcast"
    assert user.last_queue_ref_id == episode.feed_id


@pytest.mark.asyncio
async def test_upsert_state_clears_last_state(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    episode = await create_episode(db_session)
    service = WebPlayerService(session=db_session, settings=settings)

    await service.upsert_state(
        user,
        PlayerStateInput(
            episode_id=episode.id,
            position_sec=50,
            queue_mode="podcast",
            queue_ref_id=episode.feed_id,
        ),
    )
    await db_session.refresh(user)
    assert user.last_episode_id == episode.id

    await service.upsert_state(user, PlayerStateInput(episode_id=None))
    await db_session.refresh(user)

    assert user.last_episode_id is None
    assert user.last_position_sec is None
    assert user.last_queue_mode is None
    assert user.last_queue_ref_id is None
