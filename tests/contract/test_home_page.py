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


def test_home_page_logged_out_shows_login_register_and_no_logout(
    client: TestClient,
) -> None:
    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert "Malipod Selfhosted" in html
    assert "/register" in html
    assert "/login" in html
    assert 'action="/logout"' not in html
    assert "gpoddernext" not in html.lower()
    assert 'name="viewport"' in html


def test_home_page_logged_in_shows_logout_and_hides_login_register(
    client: TestClient,
) -> None:
    register_user(client)
    api_login(client)

    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert "Malipod Selfhosted" in html
    assert 'action="/logout"' in html
    assert "/register" not in html
    assert "/login" not in html
    assert "gpoddernext" not in html.lower()
