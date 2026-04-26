from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegistrationInput
from app.schemas.episode import EpisodeActionInput, EpisodeActionQuery
from app.services.auth import AuthService
from app.services.episodes import EpisodeService

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


def test_episode_action_input_rejects_invalid_progress_and_action() -> None:
    with pytest.raises(ValidationError, match="action"):
        EpisodeActionInput(
            podcast="https://example.com/feed.xml",
            episode="https://example.com/episode.mp3",
            action="bookmark",
        )

    with pytest.raises(ValidationError, match="play/pause actions require"):
        EpisodeActionInput(
            podcast="https://example.com/feed.xml",
            episode="https://example.com/episode.mp3",
            action="play",
            started=15,
            position=120,
        )

    with pytest.raises(ValidationError, match="only valid for play/pause"):
        EpisodeActionInput(
            podcast="https://example.com/feed.xml",
            episode="https://example.com/episode.mp3",
            action="download",
            total=500,
        )


def test_episode_query_validates_filters() -> None:
    query = EpisodeActionQuery(
        podcast=" https://example.com/feed.xml ",
        device="sync-box",
        since=0,
        aggregated=True,
    )

    assert query.podcast == "https://example.com/feed.xml"
    assert query.device == "sync-box"
    assert query.aggregated is True

    with pytest.raises(
        ValidationError,
        match="podcast must be an ASCII http or https URL",
    ):
        EpisodeActionQuery(podcast="ftp://example.com/feed.xml")


@pytest.mark.asyncio
async def test_episode_service_upload_tracks_update_urls_and_projection(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    service = EpisodeService(db_session)

    result = await service.upload_actions(
        user,
        [
            EpisodeActionInput(
                podcast=" https://example.com/feed.xml ",
                episode="https://example.com/episode-1.mp3 ",
                device="sync-box",
                action="download",
            ),
            EpisodeActionInput(
                podcast="https://example.com/feed.xml",
                episode="ftp://invalid.example/episode.ogg",
                action="delete",
            ),
            EpisodeActionInput(
                podcast="https://example.com/feed.xml",
                episode="https://example.com/episode-1.mp3",
                action="play",
                started=15,
                position=120,
                total=500,
            ),
        ],
    )
    read_back = await service.list_actions(user, EpisodeActionQuery())

    assert result.timestamp >= 1
    assert result.update_urls == [
        (" https://example.com/feed.xml ", "https://example.com/feed.xml"),
        ("https://example.com/episode-1.mp3 ", "https://example.com/episode-1.mp3"),
        ("ftp://invalid.example/episode.ogg", ""),
    ]
    assert [item.action for item in read_back.actions] == ["download", "play"]
    assert read_back.actions[-1].started == 15
    assert read_back.actions[-1].position == 120
    assert read_back.actions[-1].total == 500


@pytest.mark.asyncio
async def test_episode_service_filters_since_device_and_aggregated(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    service = EpisodeService(db_session)

    first = await service.upload_actions(
        user,
        [
            EpisodeActionInput(
                podcast="https://example.com/feed-a.xml",
                episode="https://example.com/episode-1.mp3",
                device="phone-01",
                action="download",
            ),
            EpisodeActionInput(
                podcast="https://example.com/feed-b.xml",
                episode="https://example.com/episode-2.mp3",
                device="tablet-01",
                action="delete",
            ),
        ],
    )
    await service.upload_actions(
        user,
        [
            EpisodeActionInput(
                podcast="https://example.com/feed-a.xml",
                episode="https://example.com/episode-1.mp3",
                device="phone-01",
                action="play",
                started=10,
                position=55,
                total=400,
            )
        ],
    )

    since_actions = await service.list_actions(
        user,
        EpisodeActionQuery(since=first.timestamp),
    )
    phone_actions = await service.list_actions(
        user,
        EpisodeActionQuery(device="phone-01"),
    )
    aggregated = await service.list_actions(
        user,
        EpisodeActionQuery(aggregated=True),
    )

    assert [item.action for item in since_actions.actions] == ["play"]
    assert [item.action for item in phone_actions.actions] == ["download", "play"]
    assert [item.episode for item in aggregated.actions] == [
        "https://example.com/episode-2.mp3",
        "https://example.com/episode-1.mp3",
    ]
    assert [item.action for item in aggregated.actions] == ["delete", "play"]
