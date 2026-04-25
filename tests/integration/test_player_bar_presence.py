from __future__ import annotations

from typing import TYPE_CHECKING

from tests.contract.test_home_page import api_login, register_user

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_player_bar_is_present_on_authenticated_pages(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get("/user/listener_1/playlists")

    assert response.status_code == 200
    assert 'id="player-bar"' in response.text
