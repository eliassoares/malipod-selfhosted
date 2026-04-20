from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_home_page_renders(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Malipod Test" in response.text
    assert "Sync your podcasts" in response.text
    assert "/register" in response.text
    assert "/login" in response.text
    assert 'action="/logout"' not in response.text
    assert "gpoddernext" not in response.text.lower()
