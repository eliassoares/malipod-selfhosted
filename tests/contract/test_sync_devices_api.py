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


def test_sync_devices_get_status_contract(client: TestClient) -> None:
    register_user(client)
    create_device(client, "listener_1", "notebook")
    create_device(client, "listener_1", "netbook")
    create_device(client, "listener_1", "pc-work")

    response = client.get(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 200
    assert response.json() == {
        "synchronized": [],
        "not-synchronized": ["netbook", "notebook", "pc-work"],
    }


def test_sync_devices_requires_authentication(client: TestClient) -> None:
    register_user(client)

    response = client.get("/api/2/sync-devices/listener_1.json")

    assert response.status_code == 401


def test_sync_devices_rejects_cross_account_access(client: TestClient) -> None:
    register_user(client, "listener_1")
    register_user(client, "listener_2")

    response = client.get(
        "/api/2/sync-devices/listener_2.json",
        auth=("listener_1", "supersecret"),
    )

    assert response.status_code == 403


def test_sync_devices_post_synchronize_and_stop_contract(client: TestClient) -> None:
    register_user(client)
    create_device(client, "listener_1", "notebook")
    create_device(client, "listener_1", "netbook")
    create_device(client, "listener_1", "pc-work")

    grouped = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"synchronize": [["notebook", "netbook"]]},
    )

    assert grouped.status_code == 200
    assert grouped.json() == {
        "synchronized": [["netbook", "notebook"]],
        "not-synchronized": ["pc-work"],
    }

    stopped = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"stop-synchronize": ["netbook"]},
    )

    assert stopped.status_code == 200
    assert stopped.json() == {
        "synchronized": [],
        "not-synchronized": ["netbook", "notebook", "pc-work"],
    }


def test_sync_devices_post_is_idempotent_and_dedupes(client: TestClient) -> None:
    register_user(client)
    create_device(client, "listener_1", "notebook")
    create_device(client, "listener_1", "netbook")

    first = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"synchronize": [["notebook", "notebook", "netbook"]]},
    )
    second = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"synchronize": [["notebook", "netbook"]]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_sync_devices_rejects_missing_device_without_partial_apply(
    client: TestClient,
) -> None:
    register_user(client)
    create_device(client, "listener_1", "notebook")
    create_device(client, "listener_1", "netbook")
    create_device(client, "listener_1", "pc-work")

    grouped = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"synchronize": [["notebook", "netbook"]]},
    )
    assert grouped.status_code == 200

    rejected = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"synchronize": [["notebook", "missing-device"]]},
    )
    assert rejected.status_code == 400
    assert rejected.json()["detail"] == "device_not_found"

    status = client.get(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
    )
    assert status.status_code == 200
    assert status.json() == {
        "synchronized": [["netbook", "notebook"]],
        "not-synchronized": ["pc-work"],
    }


def test_sync_devices_rejects_invalid_payload(client: TestClient) -> None:
    register_user(client)
    create_device(client, "listener_1", "notebook")

    response = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={"synchronize": [["notebook"]]},
    )

    assert response.status_code == 400


def test_sync_devices_post_empty_body_returns_current_status(
    client: TestClient,
) -> None:
    register_user(client)
    create_device(client, "listener_1", "notebook")
    create_device(client, "listener_1", "netbook")

    response = client.post(
        "/api/2/sync-devices/listener_1.json",
        auth=("listener_1", "supersecret"),
        json={},
    )

    assert response.status_code == 200
    assert response.json() == {
        "synchronized": [],
        "not-synchronized": ["netbook", "notebook"],
    }
