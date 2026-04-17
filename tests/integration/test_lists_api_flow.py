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


def test_create_then_read_list_across_formats(client: TestClient) -> None:
    register_user(client)

    created = client.post(
        "/api/2/lists/listener_1/create.opml?title=Backend%20Podcasts",
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
        follow_redirects=False,
    )
    summaries = client.get("/api/2/lists/listener_1.json")
    as_json = client.get("/api/2/lists/listener_1/list/backend-podcasts.json")
    as_txt = client.get("/api/2/lists/listener_1/list/backend-podcasts.txt")

    assert created.status_code == 303
    assert summaries.status_code == 200
    assert summaries.json()[0]["name"] == "backend-podcasts"
    assert [item["url"] for item in as_json.json()["podcasts"]] == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]
    assert as_txt.text.splitlines() == [
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    ]


def test_update_delete_and_missing_list_flows(client: TestClient) -> None:
    register_user(client)

    created = client.post(
        "/api/2/lists/listener_1/create.json?title=Async%20Shows",
        auth=("listener_1", "supersecret"),
        json=["https://example.com/feed-a.xml", "https://example.com/feed-b.xml"],
        follow_redirects=False,
    )
    updated = client.put(
        "/api/2/lists/listener_1/list/async-shows.json",
        auth=("listener_1", "supersecret"),
        json={"podcasts": ["https://example.com/feed-c.xml"]},
    )
    read_back = client.get("/api/2/lists/listener_1/list/async-shows.json")
    deleted = client.delete(
        "/api/2/lists/listener_1/list/async-shows.json",
        auth=("listener_1", "supersecret"),
    )
    repeated_delete = client.delete(
        "/api/2/lists/listener_1/list/async-shows.json",
        auth=("listener_1", "supersecret"),
    )

    assert created.status_code == 303
    assert updated.status_code == 204
    assert [item["url"] for item in read_back.json()["podcasts"]] == [
        "https://example.com/feed-c.xml"
    ]
    assert deleted.status_code == 204
    assert repeated_delete.status_code == 404


def test_create_and_update_reject_cross_account_and_invalid_payload(
    client: TestClient,
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")

    created = client.post(
        "/api/2/lists/listener_1/create.json?title=Python%20Weekly",
        auth=("listener_1", "supersecret"),
        json=["https://example.com/feed-a.xml"],
        follow_redirects=False,
    )
    denied = client.put(
        "/api/2/lists/listener_1/list/python-weekly.txt",
        auth=("listener_2", "supersecret"),
        content="https://example.com/feed-b.xml\n",
        headers={"Content-Type": "text/plain"},
    )
    invalid = client.post(
        "/api/2/lists/listener_1/create.json?title=Broken%20Payload",
        auth=("listener_1", "supersecret"),
        content="{bad json",
        headers={"Content-Type": "application/json"},
        follow_redirects=False,
    )

    assert created.status_code == 303
    assert denied.status_code == 403
    assert invalid.status_code == 400
