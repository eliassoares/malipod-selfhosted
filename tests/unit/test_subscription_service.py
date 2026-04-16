from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.schemas.auth import RegistrationInput
from app.services.auth import AuthService
from app.services.subscription_formats import ImportedSubscription
from app.services.subscriptions import SubscriptionError, SubscriptionService

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
async def test_subscription_service_lists_device_and_account_subscriptions_deduplicated(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    service = SubscriptionService(db_session)

    await service.replace_device_subscriptions(
        user,
        "phone-01",
        [
            ImportedSubscription(url="https://example.com/feed-a.xml", title="Feed A"),
            ImportedSubscription(url="https://example.com/feed-b.xml", title="Feed B"),
        ],
    )
    await service.replace_device_subscriptions(
        user,
        "tablet-01",
        [
            ImportedSubscription(url="https://example.com/feed-b.xml", title="Feed B"),
            ImportedSubscription(url="https://example.com/feed-c.xml", title="Feed C"),
        ],
    )

    device_items = await service.list_device_subscriptions(user, "phone-01")
    account_items = await service.list_account_subscriptions(user)

    assert [item.url for item in device_items] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]
    assert [item.url for item in account_items] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
        "https://example.com/feed-c.xml",
    ]


@pytest.mark.asyncio
async def test_subscription_service_full_upload_auto_creates_device_and_replaces_values(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    service = SubscriptionService(db_session)

    await service.replace_device_subscriptions(
        user,
        "sync-box",
        [
            ImportedSubscription(url=" https://example.com/feed-a.xml "),
            ImportedSubscription(url="https://example.com/feed-a.xml"),
            ImportedSubscription(url="ftp://ignored.example/feed"),
        ],
    )
    initial = await service.list_device_subscriptions(user, "sync-box")
    assert [item.url for item in initial] == ["https://example.com/feed-a.xml"]

    await service.replace_device_subscriptions(
        user,
        "sync-box",
        [ImportedSubscription(url="https://example.com/feed-b.xml")],
    )
    replaced = await service.list_device_subscriptions(user, "sync-box")

    assert [item.url for item in replaced] == ["https://example.com/feed-b.xml"]


@pytest.mark.asyncio
async def test_subscription_service_rejects_conflicting_delta_after_sanitization(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    service = SubscriptionService(db_session)
    await service.replace_device_subscriptions(
        user,
        "sync-box",
        [ImportedSubscription(url="https://example.com/feed-a.xml")],
    )

    with pytest.raises(SubscriptionError, match="conflicting_delta"):
        await service.apply_delta(
            user,
            "sync-box",
            [" https://example.com/feed-a.xml "],
            ["https://example.com/feed-a.xml"],
        )


@pytest.mark.asyncio
async def test_subscription_service_delta_round_trip(
    db_session: AsyncSession, settings: Settings
) -> None:
    user = await create_user(db_session, settings)
    service = SubscriptionService(db_session)
    await service.replace_device_subscriptions(
        user,
        "sync-box",
        [ImportedSubscription(url="https://example.com/feed-a.xml")],
    )
    baseline = await service.get_changes(user, "sync-box", 0)

    delta = await service.apply_delta(
        user,
        "sync-box",
        [" http://example.com/feed-b.xml ", "ftp://invalid.example/feed"],
        ["https://example.com/feed-a.xml"],
    )
    changes = await service.get_changes(user, "sync-box", baseline.timestamp)
    empty = await service.get_changes(user, "sync-box", delta.timestamp)

    assert delta.update_urls == [
        (" http://example.com/feed-b.xml ", "http://example.com/feed-b.xml"),
        ("ftp://invalid.example/feed", ""),
    ]
    assert changes.add == ["http://example.com/feed-b.xml"]
    assert changes.remove == ["https://example.com/feed-a.xml"]
    assert empty.add == []
    assert empty.remove == []
