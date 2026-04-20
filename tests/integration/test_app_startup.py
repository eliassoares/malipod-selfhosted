from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import clear_settings_cache


def test_app_starts_with_valid_configuration(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200


def test_settings_api_route_is_registered(client: TestClient) -> None:
    response = client.get("/api/2/settings/listener_1/account.json")
    assert response.status_code == 401


def test_favorites_api_route_is_registered(client: TestClient) -> None:
    response = client.get("/api/2/favorites/listener_1.json")
    assert response.status_code == 401


def test_cors_headers_present_on_responses(client: TestClient) -> None:
    response = client.get(
        "/api/v1/health/live",
        headers={"Origin": "https://example.com"},
    )
    assert response.headers.get("access-control-allow-origin") == "*"


def test_cors_preflight_returns_allow_headers(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health/live",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "*"


def test_invalid_configuration_raises_on_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "short")
    clear_settings_cache()
    from app.main import create_app

    with pytest.raises(ValidationError, match="secret_key"), TestClient(create_app()):
        pass
