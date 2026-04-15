from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def register_and_login(client: TestClient) -> None:
    client.post(
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
    client.post(
        "/login",
        data={
            "identifier": "listener@example.com",
            "password": "supersecret",
            "language_preference": "en",
        },
        follow_redirects=False,
    )


def test_profile_page_renders_for_authenticated_user(client: TestClient) -> None:
    register_and_login(client)

    response = client.get("/user/profile/listener_1")

    assert response.status_code == 200
    assert "Seu perfil" in response.text
    assert '<html lang="pt-BR">' in response.text


def test_profile_page_updates_language_preference(client: TestClient) -> None:
    register_and_login(client)

    update = client.post(
        "/user/profile/listener_1/language",
        data={"language_preference": "es"},
        follow_redirects=False,
    )
    response = client.get("/user/profile/listener_1")

    assert update.status_code == 303
    assert response.status_code == 200
    assert "Tu perfil" in response.text
    assert '<html lang="es">' in response.text
