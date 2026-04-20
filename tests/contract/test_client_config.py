from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from app.core.config import clear_settings_cache
from app.main import create_app

if TYPE_CHECKING:
    import pytest


def test_clientconfig_contract_returns_public_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://meu.servidor.com")
    clear_settings_cache()

    with TestClient(create_app()) as client:
        response = client.get("/clientconfig.json")

    assert response.status_code == 200
    payload = response.json()

    assert set(payload) == {"mygpo", "mygpo-feedservice", "update_timeout"}
    assert payload["mygpo"] == {"baseurl": "https://meu.servidor.com/"}
    assert payload["mygpo-feedservice"] == {"baseurl": "https://meu.servidor.com/"}
    assert isinstance(payload["update_timeout"], int)
    assert payload["update_timeout"] > 0


def test_clientconfig_contract_normalizes_trailing_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://meu.servidor.com////")
    clear_settings_cache()

    with TestClient(create_app()) as client:
        response = client.get("/clientconfig.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mygpo"]["baseurl"] == "https://meu.servidor.com/"


def test_clientconfig_contract_returns_json_content_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BASE_URL", "https://meu.servidor.com")
    clear_settings_cache()

    with TestClient(create_app()) as client:
        response = client.get("/clientconfig.json", headers={})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
