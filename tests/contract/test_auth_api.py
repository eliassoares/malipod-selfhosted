from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def register_user(client: TestClient) -> None:
    response = client.post(
        "/register",
        data={
            "nickname": "listener_1",
            "email": "listener@example.com",
            "password": "supersecret",
            "password_confirmation": "supersecret",
            "picture_url": "",
            "language_preference": "en",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_auth_api_login_contract(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/api/2/auth/listener_1/login.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert response.json() == {"username": "listener_1", "status": "authenticated"}
    assert "sessionid=" in response.headers.get("set-cookie", "")


def test_auth_api_login_requires_credentials(client: TestClient) -> None:
    register_user(client)

    response = client.post("/api/2/auth/listener_1/login.json")

    assert response.status_code == 401
    assert response.json()["detail"] == "login inválido"


def test_auth_api_logout_contract(client: TestClient) -> None:
    register_user(client)
    login = client.post(
        "/api/2/auth/listener_1/login.json",
        auth=("listener_1", "supersecret"),
    )

    assert login.status_code == 200

    response = client.post("/api/2/auth/listener_1/logout.json")

    assert response.status_code == 200
    assert response.json() == {"username": "listener_1", "status": "logged_out"}


def test_auth_api_rejects_cookie_for_different_user(client: TestClient) -> None:
    register_user(client)
    client.post(
        "/api/2/auth/listener_1/login.json",
        auth=("listener_1", "supersecret"),
    )

    response = client.post("/api/2/auth/other_user/logout.json")

    assert response.status_code == 400
