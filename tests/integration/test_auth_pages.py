from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_registration_page_renders(client: TestClient) -> None:
    response = client.get("/register")

    assert response.status_code == 200
    assert "Create your account" in response.text
    assert '<html lang="en">' in response.text


def test_registration_creates_account_and_redirects(client: TestClient) -> None:
    response = client.post(
        "/register",
        data={
            "nickname": "listener_1",
            "email": "listener@example.com",
            "password": "supersecret",
            "password_confirmation": "supersecret",
            "picture_url": "https://example.com/avatar.png",
            "language_preference": "es",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?created=1"
    assert "malipod_locale=es" in response.headers.get("set-cookie", "")


def test_registration_rejects_duplicate_user(client: TestClient) -> None:
    payload = {
        "nickname": "listener_1",
        "email": "listener@example.com",
        "password": "supersecret",
        "password_confirmation": "supersecret",
        "picture_url": "https://example.com/avatar.png",
        "language_preference": "en",
    }
    first = client.post("/register", data=payload, follow_redirects=False)
    second = client.post("/register", data=payload)

    assert first.status_code == 303
    assert second.status_code == 400
    assert "user already exists" in second.text


def test_registration_rejects_invalid_nickname(client: TestClient) -> None:
    response = client.post(
        "/register",
        data={
            "nickname": "bad!",
            "email": "listener@example.com",
            "password": "supersecret",
            "password_confirmation": "supersecret",
            "picture_url": "",
            "language_preference": "en",
        },
    )

    assert response.status_code == 400
    assert "nickname" in response.text.lower()
