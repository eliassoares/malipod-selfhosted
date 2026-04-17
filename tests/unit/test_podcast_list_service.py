from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.schemas.auth import RegistrationInput
from app.schemas.podcast_list import PodcastListEntry, PodcastListRenderPayload
from app.services.auth import AuthService
from app.services.podcast_lists import PodcastListError, PodcastListService
from app.services.subscription_formats import SubscriptionFormatService

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
async def test_podcast_list_service_creates_slug_conflict_and_summary_read(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    username = user.nickname
    service = PodcastListService(db_session)

    location = await service.create_list(
        user,
        title="My Python Podcasts",
        format_name="json",
        body=b'["https://example.com/feed-a.xml", "https://example.com/feed-b.xml"]',
    )

    assert location == "/api/2/lists/listener_1/list/my-python-podcasts.json"

    summaries = await service.list_summaries(username)
    document = await service.get_document(username, "my-python-podcasts", "json")
    rendered = service.format_service.render_list(document)

    assert [item.name for item in summaries] == ["my-python-podcasts"]
    assert (
        summaries[0].web
        == "http://gpodder.net/user/listener_1/lists/my-python-podcasts"
    )
    assert rendered.content["name"] == "my-python-podcasts"
    assert [item["url"] for item in rendered.content["podcasts"]] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]

    with pytest.raises(PodcastListError, match="name_conflict"):
        await service.create_list(
            user,
            title="My Python Podcasts",
            format_name="txt",
            body=b"https://example.com/feed-c.xml\n",
        )


@pytest.mark.asyncio
async def test_podcast_list_service_uses_fallback_slug_and_deduplicates_entries(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    username = user.nickname
    service = PodcastListService(db_session)

    location = await service.create_list(
        user,
        title="!!!",
        format_name="txt",
        body=(
            b"https://example.com/feed-a.xml\n"
            b" https://example.com/feed-a.xml \n"
            b"ftp://invalid.example/feed\n"
        ),
    )
    document = await service.get_document(username, "list", "txt")
    rendered = service.format_service.render_list(document)

    assert location == "/api/2/lists/listener_1/list/list.txt"
    assert rendered.content == "https://example.com/feed-a.xml\n"


@pytest.mark.asyncio
async def test_podcast_list_service_updates_and_deletes_list(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    username = user.nickname
    service = PodcastListService(db_session)
    await service.create_list(
        user,
        title="Async Shows",
        format_name="json",
        body=b'["https://example.com/feed-a.xml", "https://example.com/feed-b.xml"]',
    )

    await service.update_list(
        user,
        listname="async-shows",
        format_name="json",
        body=(
            b'{"podcasts": ['
            b'{"url": "https://example.com/feed-c.xml", "title": "Feed C"},'
            b'"https://example.com/feed-a.xml"'
            b"]}"
        ),
    )
    updated = await service.get_document(username, "async-shows", "opml")
    rendered = service.format_service.render_list(updated)

    assert "https://example.com/feed-c.xml" in rendered.content
    assert "https://example.com/feed-a.xml" in rendered.content

    await service.delete_list(user, "async-shows")

    with pytest.raises(PodcastListError, match="list_not_found"):
        await service.get_document(username, "async-shows", "json")


def test_subscription_format_service_parses_and_renders_podcast_list_formats() -> None:
    service = SubscriptionFormatService()

    parsed = service.parse_list_upload(
        "json",
        (
            b'{"podcasts": ['
            b'{"url": "https://example.com/feed-1.xml", "title": "Feed One"},'
            b'"https://example.com/feed-2.xml"'
            b"]}"
        ),
    )
    rendered = service.render_list(
        PodcastListRenderPayload(
            title="Example List",
            name="example-list",
            items=[
                PodcastListEntry(
                    url="https://example.com/feed-1.xml",
                    title="Feed One",
                ),
                PodcastListEntry(url="https://example.com/feed-2.xml"),
            ],
            format="txt",
        )
    )

    assert [item.url for item in parsed] == [
        "https://example.com/feed-1.xml",
        "https://example.com/feed-2.xml",
    ]
    assert rendered.content == (
        "https://example.com/feed-1.xml\nhttps://example.com/feed-2.xml\n"
    )
