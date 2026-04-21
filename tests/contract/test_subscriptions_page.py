from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.contract.test_home_page import api_login, register_user
from tests.shared.subscriptions_helpers import (
    add_episode,
    create_feed,
    days_ago,
    ensure_device,
    get_user,
    subscribe,
)

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession


def test_subscriptions_page_logged_out_redirects_to_login(client: TestClient) -> None:
    response = client.get("/user/subscriptions/listener_1", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_subscriptions_preferences_logged_out_redirects_to_login(
    client: TestClient,
) -> None:
    response = client.post(
        "/user/subscriptions/listener_1/preferences",
        data={"view_mode": "grid", "sort": "recent"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_subscriptions_page_username_mismatch_returns_404(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get(
        "/user/subscriptions/other_user",
        follow_redirects=False,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_subscriptions_page_renders_items_and_empty_state(
    client: TestClient,
    db_session: AsyncSession,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")
    user = await get_user(db_session, "listener_1")

    response = client.get(f"/user/subscriptions/{user.nickname}")
    assert response.status_code == 200
    assert (
        "No subscriptions" in response.text or "Você ainda não segue" in response.text
    )

    device = await ensure_device(db_session, user, device_id="device-1")
    feed_a = await create_feed(
        db_session,
        feed_url="https://example.com/a.xml",
        title="Alpha Podcast",
    )
    await subscribe(db_session, device=device, feed=feed_a)
    await add_episode(
        db_session,
        feed=feed_a,
        episode_url="https://example.com/a/1",
        title="Alpha Ep 1",
        released_at=days_ago(2),
    )

    feed_b = await create_feed(
        db_session,
        feed_url="https://example.com/b.xml",
        title="Beta Podcast",
    )
    await subscribe(db_session, device=device, feed=feed_b)
    await add_episode(
        db_session,
        feed=feed_b,
        episode_url="https://example.com/b/1",
        title="Beta Ep 1",
        released_at=days_ago(10),
    )

    response = client.get(f"/user/subscriptions/{user.nickname}")
    assert response.status_code == 200
    html = response.text
    assert "Alpha Podcast" in html
    assert "Beta Podcast" in html
    assert "/static/placeholders/" in html


@pytest.mark.asyncio
async def test_subscriptions_search_filters_results(
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

    response = client.get(f"/user/subscriptions/{user.nickname}?q=alpha")
    assert response.status_code == 200
    html = response.text.lower()
    assert "alpha podcast" in html
    assert "beta podcast" not in html


@pytest.mark.asyncio
async def test_subscriptions_sorting_recent_and_oldest(
    client: TestClient,
    db_session: AsyncSession,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")
    user = await get_user(db_session, "listener_1")
    device = await ensure_device(db_session, user, device_id="device-1")

    feed_recent = await create_feed(
        db_session,
        feed_url="https://example.com/recent.xml",
        title="Recent Podcast",
    )
    feed_old = await create_feed(
        db_session,
        feed_url="https://example.com/old.xml",
        title="Old Podcast",
    )
    await subscribe(db_session, device=device, feed=feed_recent)
    await subscribe(db_session, device=device, feed=feed_old)
    await add_episode(
        db_session,
        feed=feed_recent,
        episode_url="https://example.com/recent/1",
        title="Recent Ep 1",
        released_at=days_ago(1),
    )
    await add_episode(
        db_session,
        feed=feed_old,
        episode_url="https://example.com/old/1",
        title="Old Ep 1",
        released_at=days_ago(20),
    )

    recent_html = client.get(f"/user/subscriptions/{user.nickname}?sort=recent").text
    assert recent_html.index("Recent Podcast") < recent_html.index("Old Podcast")

    oldest_html = client.get(f"/user/subscriptions/{user.nickname}?sort=oldest").text
    assert oldest_html.index("Old Podcast") < oldest_html.index("Recent Podcast")


@pytest.mark.asyncio
async def test_subscriptions_preferences_persist_view_mode(
    client: TestClient,
    db_session: AsyncSession,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    user = await get_user(db_session, "listener_1")
    device = await ensure_device(db_session, user, device_id="device-1")
    feed = await create_feed(
        db_session,
        feed_url="https://example.com/a.xml",
        title="Alpha Podcast",
    )
    await subscribe(db_session, device=device, feed=feed)
    await add_episode(
        db_session,
        feed=feed,
        episode_url="https://example.com/a/1",
        title="Alpha Ep 1",
        released_at=days_ago(1),
    )

    response = client.post(
        "/user/subscriptions/listener_1/preferences",
        data={"view_mode": "grid", "sort": "recent"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    html = client.get("/user/subscriptions/listener_1").text
    assert 'data-view="grid"' in html
