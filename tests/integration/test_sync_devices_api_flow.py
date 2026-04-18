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


def create_device(client: TestClient, username: str, device_id: str) -> None:
    response = client.post(
        f"/api/2/devices/{username}/{device_id}.json",
        auth=(username, "supersecret"),
        json={"caption": device_id, "type": "desktop"},
    )
    assert response.status_code == 200


def test_sync_devices_end_to_end_flow(client: TestClient) -> None:
    register_user(client)
    create_device(client, "listener_1", "notebook")
    create_device(client, "listener_1", "netbook")
    create_device(client, "listener_1", "pc-work")

    baseline = client.get(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
    )
    assert baseline.status_code == 200
    assert baseline.json()["synchronized"] == []

    grouped = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"synchronize": [["notebook", "netbook"]]},
    )
    assert grouped.status_code == 200
    assert grouped.json()["synchronized"] == [["netbook", "notebook"]]

    stopped = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"stop-synchronize": ["netbook"]},
    )
    assert stopped.status_code == 200
    assert stopped.json()["synchronized"] == []
