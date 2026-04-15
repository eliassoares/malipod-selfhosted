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
            "language_preference": "pt-BR",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_login_redirects_to_profile_and_sets_cookie(client: TestClient) -> None:
    register_user(client)

    response = client.post(
        "/login",
        data={
            "identifier": "listener@example.com",
            "password": "supersecret",
            "language_preference": "es",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/user/profile/listener_1"
    cookies = response.headers.get("set-cookie", "")
    assert "sessionid=" in cookies
    assert "malipod_locale=pt-BR" in cookies


def test_login_returns_generic_error_for_invalid_credentials(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.post(
        "/login",
        data={
            "identifier": "listener@example.com",
            "password": "wrongpass",
            "language_preference": "en",
        },
    )

    assert response.status_code == 401
    assert "login inválido" in response.text


def test_logout_revokes_session(client: TestClient) -> None:
    register_user(client)
    login_response = client.post(
        "/login",
        data={
            "identifier": "listener@example.com",
            "password": "supersecret",
            "language_preference": "en",
        },
        follow_redirects=False,
    )

    assert login_response.status_code == 303

    logout_response = client.post("/logout", follow_redirects=False)

    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/login"

    profile_response = client.get("/user/profile/listener_1", follow_redirects=False)
    assert profile_response.status_code == 303
    assert profile_response.headers["location"] == "/login"
