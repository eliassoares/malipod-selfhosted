from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from app.db.models.podcast import EpisodeModel, FavoriteEpisodeModel, PodcastFeedModel
from app.schemas.auth import RegistrationInput
from app.services.auth import AuthService
from app.services.favorites import FavoritesError, FavoritesService

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
async def test_favorites_service_returns_ordered_serialized_items(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    service = FavoritesService(db_session)
    now = datetime.now(UTC)

    feed_one = PodcastFeedModel(
        feed_url="https://example.com/feed-a.xml",
        title="Feed A",
        description=None,
        website=None,
        logo_url=None,
        mygpo_link=None,
        created_at=now,
        updated_at=now,
    )
    feed_two = PodcastFeedModel(
        feed_url="https://example.com/feed-b.xml",
        title="Feed B",
        description=None,
        website=None,
        logo_url=None,
        mygpo_link=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([feed_one, feed_two])
    await db_session.flush()

    episode_one = EpisodeModel(
        feed_id=feed_one.id,
        episode_url="https://example.com/episode-a.mp3",
        title="Episode A",
        description="Description A",
        website="https://example.com/a",
        mygpo_link="https://gpodder.net/episode/a",
        released_at=now - timedelta(days=2),
        created_at=now,
        updated_at=now,
    )
    episode_two = EpisodeModel(
        feed_id=feed_two.id,
        episode_url="https://example.com/episode-b.mp3",
        title="Episode B",
        description=None,
        website=None,
        mygpo_link=None,
        released_at=now - timedelta(days=1),
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([episode_one, episode_two])
    await db_session.flush()

    db_session.add_all(
        [
            FavoriteEpisodeModel(
                user_id=user.id,
                episode_id=episode_two.id,
                favorited_at=now - timedelta(hours=3),
                created_at=now,
                updated_at=now,
            ),
            FavoriteEpisodeModel(
                user_id=user.id,
                episode_id=episode_one.id,
                favorited_at=now,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    await db_session.commit()

    result = await service.list_favorites(user, username=user.nickname)

    assert [item.title for item in result] == ["Episode A", "Episode B"]
    assert result[0].podcast_title == "Feed A"
    assert result[0].description == "Description A"
    assert result[1].description is None


@pytest.mark.asyncio
async def test_favorites_service_returns_empty_list_for_user_without_favorites(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    user = await create_user(db_session, settings)
    service = FavoritesService(db_session)

    result = await service.list_favorites(user, username=user.nickname)

    assert result == []


@pytest.mark.asyncio
async def test_favorites_service_raises_for_foreign_and_missing_users(
    db_session: AsyncSession,
    settings: Settings,
) -> None:
    owner = await create_user(db_session, settings)
    other = await create_user(
        db_session,
        settings,
        nickname="listener_2",
        email="listener2@example.com",
    )
    service = FavoritesService(db_session)

    with pytest.raises(FavoritesError, match="forbidden"):
        await service.list_favorites(other, username=owner.nickname)

    with pytest.raises(FavoritesError, match="target_not_found"):
        await service.list_favorites(other, username="missing-user")
