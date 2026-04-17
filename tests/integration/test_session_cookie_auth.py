from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def register_user(client: TestClient, nickname: str = "listener_1") -> None:
    response = client.post(
        "/register",
        data={
            "nickname": nickname,
            "email": f"{nickname}@example.com",
            "password": "supersecret",
            "password_confirmation": "supersecret",
            "picture_url": "",
            "language_preference": "en",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def api_login(client: TestClient, nickname: str = "listener_1") -> None:
    response = client.post(
        f"/api/2/auth/{nickname}/login.json",
        auth=(nickname, "supersecret"),
    )
    assert response.status_code == 200
    assert "sessionid" in client.cookies


def test_session_cookie_authenticates_devices_endpoint(
    client: TestClient,
) -> None:
    register_user(client)
    api_login(client)

    response = client.get("/api/2/devices/listener_1.json")

    assert response.status_code == 200


def test_session_cookie_authenticates_subscriptions_endpoint(
    client: TestClient,
) -> None:
    register_user(client)
    api_login(client)

    response = client.get("/subscriptions/listener_1.json")

    assert response.status_code == 200


def test_session_cookie_authenticates_episodes_endpoint(
    client: TestClient,
) -> None:
    register_user(client)
    api_login(client)

    response = client.post(
        "/api/2/episodes/listener_1.json",
        json=[
            {
                "podcast": "https://example.com/feed.xml",
                "episode": "https://example.com/ep.mp3",
                "action": "download",
            }
        ],
    )

    assert response.status_code == 200


def test_session_cookie_authenticates_settings_endpoint(
    client: TestClient,
) -> None:
    register_user(client)
    api_login(client)

    response = client.get("/api/2/settings/listener_1/account.json")

    assert response.status_code == 200


def test_session_cookie_rejects_mismatched_username(
    client: TestClient,
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")
    api_login(client)

    response = client.get("/api/2/devices/listener_2.json")

    assert response.status_code == 403


def test_no_credentials_returns_401(client: TestClient) -> None:
    register_user(client)

    response = client.get("/api/2/devices/listener_1.json")

    assert response.status_code == 401
