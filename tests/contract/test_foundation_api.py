from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_api_root_contract(client: TestClient) -> None:
    response = client.get("/api/v1")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"name", "status", "docs"}
    assert payload["status"] == "ready"


def test_liveness_contract(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_contract(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert len(payload["checks"]) >= 2
