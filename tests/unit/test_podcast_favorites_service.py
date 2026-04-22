from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.db.models.podcast import PodcastFeedModel
from app.schemas.auth import RegistrationInput
from app.services.auth import AuthService
from app.services.podcast_favorites import PodcastFavoritesService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings
    from app.db.models.user import UserModel


def build_registration(
    nickname: str = "listener_1",
    email: str = "listener@example.com",
) -> RegistrationInput:
    return RegistrationInput(
        nickname=nickname,
        email=email,
        password="supersecret",
        password_confirmation="supersecret",
        picture_url="",
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
async def test_podcast_favorites_toggle_and_list(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    now = datetime.now(UTC)
    feed = PodcastFeedModel(
        feed_url="https://example.com/feed.xml",
        title="Example Feed",
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

    service = PodcastFavoritesService(db_session)

    assert await service.is_favorited(user, feed_id=feed.id) is False
    assert await service.list_favorite_feed_ids(user) == set()

    after_add = await service.toggle_favorite(user, feed_id=feed.id)
    assert after_add is True
    assert await service.is_favorited(user, feed_id=feed.id) is True
    assert await service.list_favorite_feed_ids(user) == {feed.id}

    after_remove = await service.toggle_favorite(user, feed_id=feed.id)
    assert after_remove is False
    assert await service.is_favorited(user, feed_id=feed.id) is False
    assert await service.list_favorite_feed_ids(user) == set()
