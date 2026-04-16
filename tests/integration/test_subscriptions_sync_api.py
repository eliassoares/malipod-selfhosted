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


def test_full_upload_then_read_across_formats(client: TestClient) -> None:
    register_user(client)

    uploaded = client.put(
        "/subscriptions/listener_1/sync-box.opml",
        auth=("listener_1", "supersecret"),
        content="""<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <body>
    <outline text="Feed A" xmlUrl="https://example.com/feed-a.xml" />
    <outline text="Feed B" xmlUrl="https://example.com/feed-b.xml" />
  </body>
</opml>
""",
        headers={"Content-Type": "application/xml"},
    )
    as_json = client.get(
        "/subscriptions/listener_1/sync-box.json",
        auth=("listener_1", "supersecret"),
    )
    as_txt = client.get(
        "/subscriptions/listener_1/sync-box.txt",
        auth=("listener_1", "supersecret"),
    )
    account = client.get(
        "/subscriptions/listener_1.json",
        auth=("listener_1", "supersecret"),
    )

    assert uploaded.status_code == 200
    assert uploaded.content == b""
    assert [item["url"] for item in as_json.json()] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]
    assert as_txt.text.splitlines() == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]
    assert [item["url"] for item in account.json()] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]


def test_full_upload_replaces_previous_values_and_enforces_ownership(
    client: TestClient,
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")

    first = client.put(
        "/subscriptions/listener_1/sync-box.txt",
        auth=("listener_1", "supersecret"),
        content="https://example.com/feed-a.xml\nhttps://example.com/feed-b.xml\n",
        headers={"Content-Type": "text/plain"},
    )
    replaced = client.put(
        "/subscriptions/listener_1/sync-box.json",
        auth=("listener_1", "supersecret"),
        json=["https://example.com/feed-c.xml"],
    )
    denied = client.put(
        "/subscriptions/listener_1/sync-box.txt",
        auth=("listener_2", "supersecret"),
        content="https://example.com/feed-z.xml\n",
        headers={"Content-Type": "text/plain"},
    )
    read_back = client.get(
        "/subscriptions/listener_1/sync-box.json",
        auth=("listener_1", "supersecret"),
    )

    assert first.status_code == 200
    assert replaced.status_code == 200
    assert denied.status_code == 403
    assert [item["url"] for item in read_back.json()] == [
        "https://example.com/feed-c.xml"
    ]


def test_delta_sync_round_trip_returns_only_newer_changes(client: TestClient) -> None:
    register_user(client)

    seeded = client.put(
        "/subscriptions/listener_1/sync-box.txt",
        auth=("listener_1", "supersecret"),
        content="https://example.com/feed-a.xml\n",
        headers={"Content-Type": "text/plain"},
    )
    baseline = client.get(
        "/api/2/subscriptions/listener_1/sync-box.json?since=0",
        auth=("listener_1", "supersecret"),
    )
    delta = client.post(
        "/api/2/subscriptions/listener_1/sync-box.json",
        auth=("listener_1", "supersecret"),
        json={
            "add": [" https://example.com/feed-b.xml ", "ftp://invalid.example/feed"],
            "remove": ["https://example.com/feed-a.xml"],
        },
    )
    changes = client.get(
        f"/api/2/subscriptions/listener_1/sync-box.json?since={baseline.json()['timestamp']}",
        auth=("listener_1", "supersecret"),
    )
    empty = client.get(
        f"/api/2/subscriptions/listener_1/sync-box.json?since={delta.json()['timestamp']}",
        auth=("listener_1", "supersecret"),
    )

    assert seeded.status_code == 200
    assert delta.status_code == 200
    assert delta.json()["update_urls"] == [
        [" https://example.com/feed-b.xml ", "https://example.com/feed-b.xml"],
        ["ftp://invalid.example/feed", ""],
    ]
    assert changes.json()["add"] == ["https://example.com/feed-b.xml"]
    assert changes.json()["remove"] == ["https://example.com/feed-a.xml"]
    assert empty.json()["add"] == []
    assert empty.json()["remove"] == []


def test_device_read_rejects_unknown_device_and_invalid_format(
    client: TestClient,
) -> None:
    register_user(client)

    invalid_format = client.get(
        "/subscriptions/listener_1/sync-box.xml",
        auth=("listener_1", "supersecret"),
    )
    missing_device = client.get(
        "/subscriptions/listener_1/sync-box.json",
        auth=("listener_1", "supersecret"),
    )

    assert invalid_format.status_code == 400
    assert missing_device.status_code == 404
