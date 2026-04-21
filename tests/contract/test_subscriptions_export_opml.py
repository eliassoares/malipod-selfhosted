from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

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
async def test_export_opml_downloads_all_feeds(
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

    response = client.get(f"/user/subscriptions/{user.nickname}/export.opml")
    assert response.status_code == 200
    assert "application/xml" in response.headers.get("content-type", "")
    assert "attachment" in response.headers.get("content-disposition", "")
    body = response.text
    assert "<opml" in body.lower()
    assert "https://example.com/a.xml" in body
    assert "https://example.com/b.xml" in body
