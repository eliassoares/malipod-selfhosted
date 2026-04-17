from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.db.models.device import DeviceModel
from app.db.models.podcast import EpisodeModel, PodcastFeedModel
from app.schemas.auth import RegistrationInput
from app.schemas.setting import SettingsMutationRequest, SettingsScopeQuery
from app.services.auth import AuthService
from app.services.settings import SettingsError, SettingsService

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


async def seed_scope_targets(db_session: AsyncSession, user: UserModel) -> None:
    now = datetime.now(UTC)
    device = DeviceModel(
        user_id=user.id,
        device_id="phone-01",
        caption="Phone",
        device_type="mobile",
        created_at=now,
        updated_at=now,
    )
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
    db_session.add_all([device, feed])
    await db_session.flush()
    episode = EpisodeModel(
        feed_id=feed.id,
        episode_url="https://example.com/episode-1.mp3",
        title="Episode 1",
        description=None,
        website=None,
        mygpo_link=None,
        released_at=now,
        created_at=now,
        updated_at=now,
    )
    db_session.add(episode)
    await db_session.commit()


@pytest.mark.asyncio
async def test_settings_service_returns_empty_documents_for_valid_targets(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    await seed_scope_targets(db_session, user)
    service = SettingsService(db_session)

    account = await service.get_settings(user, SettingsScopeQuery(scope="account"))
    device = await service.get_settings(
        user, SettingsScopeQuery(scope="device", device="phone-01")
    )
    podcast = await service.get_settings(
        user,
        SettingsScopeQuery(scope="podcast", podcast="https://example.com/feed.xml"),
    )
    episode = await service.get_settings(
        user,
        SettingsScopeQuery(
            scope="episode",
            podcast="https://example.com/feed.xml",
            episode="https://example.com/episode-1.mp3",
        ),
    )

    assert account.root == {}
    assert device.root == {}
    assert podcast.root == {}
    assert episode.root == {}


@pytest.mark.asyncio
async def test_settings_service_saves_and_removes_values_atomically(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    await seed_scope_targets(db_session, user)
    service = SettingsService(db_session)

    created = await service.save_settings(
        user,
        SettingsScopeQuery(scope="account"),
        SettingsMutationRequest(
            set={"public_profile": False, "store_user_agent": True},
            remove=[],
        ),
    )
    updated = await service.save_settings(
        user,
        SettingsScopeQuery(scope="account"),
        SettingsMutationRequest(
            set={"custom": {"level": 2}},
            remove=["store_user_agent"],
        ),
    )

    assert created.root == {"public_profile": False, "store_user_agent": True}
    assert updated.root == {"public_profile": False, "custom": {"level": 2}}


@pytest.mark.asyncio
async def test_settings_service_round_trips_known_and_nested_json_values(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    await seed_scope_targets(db_session, user)
    service = SettingsService(db_session)

    saved = await service.save_settings(
        user,
        SettingsScopeQuery(
            scope="episode",
            podcast="https://example.com/feed.xml",
            episode="https://example.com/episode-1.mp3",
        ),
        SettingsMutationRequest(
            set={
                "is_favorite": True,
                "bookmark": {"position": 123, "labels": ["a", "b"], "extra": None},
            },
            remove=[],
        ),
    )
    read_back = await service.get_settings(
        user,
        SettingsScopeQuery(
            scope="episode",
            podcast="https://example.com/feed.xml",
            episode="https://example.com/episode-1.mp3",
        ),
    )

    assert saved.root["is_favorite"] is True
    assert read_back.root == {
        "is_favorite": True,
        "bookmark": {"position": 123, "labels": ["a", "b"], "extra": None},
    }


@pytest.mark.asyncio
async def test_settings_service_raises_for_missing_targets(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    service = SettingsService(db_session)

    with pytest.raises(SettingsError, match="target_not_found"):
        await service.get_settings(
            user,
            SettingsScopeQuery(scope="device", device="missing-device"),
        )
