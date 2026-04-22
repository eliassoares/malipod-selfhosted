from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from app.db.models.podcast import FavoritePodcastModel
from tests.contract.test_home_page import api_login, register_user
from tests.shared.subscriptions_helpers import (
    create_feed,
    ensure_device,
    get_user,
    subscribe,
)

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_subscriptions_page_filters_to_favorites_only(
    client: TestClient,
    db_session: AsyncSession,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")
    user = await get_user(db_session, "listener_1")
    device = await ensure_device(db_session, user, device_id="device-1")

    feed_a = await create_feed(
        db_session,
        feed_url="https://example.com/a.xml",
        title="Alpha Podcast",
    )
    feed_b = await create_feed(
        db_session,
        feed_url="https://example.com/b.xml",
        title="Beta Podcast",
    )
    await subscribe(db_session, device=device, feed=feed_a)
    await subscribe(db_session, device=device, feed=feed_b)

    now = datetime.now(UTC)
    db_session.add(
        FavoritePodcastModel(
            user_id=user.id,
            feed_id=feed_a.id,
            favorited_at=now,
            created_at=now,
            updated_at=now,
        )
    )
    await db_session.commit()

    html = client.get(f"/user/subscriptions/{user.nickname}?favorites=1").text
    assert "Alpha Podcast" in html
    assert "Beta Podcast" not in html


@pytest.mark.asyncio
async def test_subscriptions_page_favorites_filter_shows_empty_state(
    client: TestClient,
    db_session: AsyncSession,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")
    user = await get_user(db_session, "listener_1")
    device = await ensure_device(db_session, user, device_id="device-1")

    feed_a = await create_feed(
        db_session,
        feed_url="https://example.com/a.xml",
        title="Alpha Podcast",
    )
    await subscribe(db_session, device=device, feed=feed_a)

    response = client.get(f"/user/subscriptions/{user.nickname}?favorites=1")
    assert response.status_code == 200
    assert "No favorites" in response.text or "Nenhum favorito" in response.text
