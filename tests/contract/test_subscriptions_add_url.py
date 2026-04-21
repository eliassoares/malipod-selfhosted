from __future__ import annotations

from typing import TYPE_CHECKING

from tests.contract.test_home_page import api_login, register_user

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_add_subscription_logged_out_redirects_to_login(client: TestClient) -> None:
    response = client.post(
        "/user/subscriptions/listener_1/add",
        data={"feed_url": "https://example.com/feed.xml"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_add_subscription_rejects_invalid_url(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.post(
        "/user/subscriptions/listener_1/add",
        data={"feed_url": "notaurl"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error=invalid_url" in response.headers["location"]


def test_add_subscription_creates_subscription_and_rejects_duplicate(
    client: TestClient,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.post(
        "/user/subscriptions/listener_1/add",
        data={"feed_url": "https://example.com/feed.xml"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "success=added" in response.headers["location"]

    duplicate = client.post(
        "/user/subscriptions/listener_1/add",
        data={"feed_url": "https://example.com/feed.xml"},
        follow_redirects=False,
    )
    assert duplicate.status_code == 303
    assert "error=duplicate" in duplicate.headers["location"]
