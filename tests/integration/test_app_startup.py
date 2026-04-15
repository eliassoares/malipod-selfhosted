from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import clear_settings_cache


def test_app_starts_with_valid_configuration(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200


def test_invalid_configuration_raises_on_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "short")
    clear_settings_cache()
    from app.main import create_app

    with pytest.raises(ValidationError, match="secret_key"), TestClient(create_app()):
        pass
