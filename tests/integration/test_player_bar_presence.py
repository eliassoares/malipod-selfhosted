from __future__ import annotations

from typing import TYPE_CHECKING

from tests.contract.test_home_page import api_login, register_user

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

_PLAYER_BAR_MARKER = 'id="player-bar"'


def test_player_bar_is_present_on_playlists_page(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get("/user/listener_1/playlists")

    assert response.status_code == 200
    assert _PLAYER_BAR_MARKER in response.text


def test_player_bar_is_present_on_home_page(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get("/")

    assert response.status_code == 200
    assert _PLAYER_BAR_MARKER in response.text


def test_player_bar_is_present_on_subscriptions_page(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get("/user/subscriptions/listener_1")

    assert response.status_code == 200
    assert _PLAYER_BAR_MARKER in response.text


def test_player_bar_is_present_on_profile_page(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get("/user/profile/listener_1")

    assert response.status_code == 200
    assert _PLAYER_BAR_MARKER in response.text
