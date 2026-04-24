from __future__ import annotations

import re
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


def test_profile_page_updates_centralize_sync_preference(client: TestClient) -> None:
    register_and_login(client)

    enabled = client.post(
        "/user/profile/listener_1/centralize-sync",
        data={"centralize_sync": "1"},
        follow_redirects=False,
    )
    page_enabled = client.get("/user/profile/listener_1")
    disabled = client.post(
        "/user/profile/listener_1/centralize-sync",
        data={},
        follow_redirects=False,
    )
    page_disabled = client.get("/user/profile/listener_1")

    assert enabled.status_code == 303
    assert page_enabled.status_code == 200
    assert re.search(
        r'<input[^>]*name="centralize_sync"[^>]*checked', page_enabled.text
    )
    assert disabled.status_code == 303
    assert page_disabled.status_code == 200
    assert 'name="centralize_sync"' in page_disabled.text
    assert not re.search(
        r'<input[^>]*name="centralize_sync"[^>]*checked', page_disabled.text
    )


def test_profile_page_centralize_sync_toggle_is_owner_only(
    client: TestClient,
) -> None:
    register_and_login(client)
    client.post(
        "/register",
        data={
            "nickname": "listener_2",
            "email": "listener_2@example.com",
            "password": "supersecret",
            "password_confirmation": "supersecret",
            "picture_url": "",
            "language_preference": "en",
        },
        follow_redirects=False,
    )

    response = client.post(
        "/user/profile/listener_2/centralize-sync",
        data={"centralize_sync": "1"},
        follow_redirects=False,
    )

    assert response.status_code == 404
