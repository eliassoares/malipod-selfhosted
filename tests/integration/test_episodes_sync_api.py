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


def test_episode_upload_and_incremental_read_round_trip(client: TestClient) -> None:
    register_user(client)

    first = client.post(
        "/api/2/episodes/listener_1.json",
        auth=("listener_1", "supersecret"),
        json=[
            {
                "podcast": "https://example.com/feed.xml",
                "episode": "https://example.com/episode-1.mp3",
                "device": "phone-01",
                "action": "download",
            }
        ],
    )
    baseline = client.get(
        "/api/2/episodes/listener_1.json?since=0",
        auth=("listener_1", "supersecret"),
    )
    second = client.post(
        "/api/2/episodes/listener_1.json",
        auth=("listener_1", "supersecret"),
        json=[
            {
                "podcast": "https://example.com/feed.xml",
                "episode": "https://example.com/episode-1.mp3",
                "device": "phone-01",
                "action": "play",
                "started": 10,
                "position": 99,
                "total": 200,
            }
        ],
    )
    incremental = client.get(
        f"/api/2/episodes/listener_1.json?since={baseline.json()['timestamp']}",
        auth=("listener_1", "supersecret"),
    )
    empty = client.get(
        f"/api/2/episodes/listener_1.json?since={second.json()['timestamp']}",
        auth=("listener_1", "supersecret"),
    )

    assert first.status_code == 200
    assert baseline.status_code == 200
    assert len(baseline.json()["actions"]) == 1
    assert incremental.status_code == 200
    assert [item["action"] for item in incremental.json()["actions"]] == ["play"]
    assert empty.status_code == 200
    assert empty.json()["actions"] == []


def test_episode_filters_and_aggregation_work_together(client: TestClient) -> None:
    register_user(client)

    client.post(
        "/api/2/episodes/listener_1.json",
        auth=("listener_1", "supersecret"),
        json=[
            {
                "podcast": "https://example.com/feed-a.xml",
                "episode": "https://example.com/episode-1.mp3",
                "device": "phone-01",
                "action": "download",
            },
            {
                "podcast": "https://example.com/feed-a.xml",
                "episode": "https://example.com/episode-1.mp3",
                "device": "phone-01",
                "action": "play",
                "started": 1,
                "position": 20,
                "total": 300,
            },
            {
                "podcast": "https://example.com/feed-b.xml",
                "episode": "https://example.com/episode-2.mp3",
                "device": "tablet-01",
                "action": "delete",
            },
        ],
    )

    by_device = client.get(
        "/api/2/episodes/listener_1.json?device=phone-01",
        auth=("listener_1", "supersecret"),
    )
    by_podcast = client.get(
        "/api/2/episodes/listener_1.json?podcast=https://example.com/feed-a.xml",
        auth=("listener_1", "supersecret"),
    )
    aggregated = client.get(
        "/api/2/episodes/listener_1.json?aggregated=true",
        auth=("listener_1", "supersecret"),
    )

    assert [item["action"] for item in by_device.json()["actions"]] == [
        "download",
        "play",
    ]
    assert [item["action"] for item in by_podcast.json()["actions"]] == [
        "download",
        "play",
    ]
    assert [item["action"] for item in aggregated.json()["actions"]] == [
        "play",
        "delete",
    ]


def test_episode_upload_rejects_incomplete_play_and_enforces_ownership(
    client: TestClient,
) -> None:
    register_user(client)
    register_user(client, nickname="listener_2")

    invalid = client.post(
        "/api/2/episodes/listener_1.json",
        auth=("listener_1", "supersecret"),
        json=[
            {
                "podcast": "https://example.com/feed.xml",
                "episode": "https://example.com/episode-1.mp3",
                "action": "play",
                "position": 30,
                "total": 90,
            }
        ],
    )
    denied = client.get(
        "/api/2/episodes/listener_1.json",
        auth=("listener_2", "supersecret"),
    )

    assert invalid.status_code == 400
    assert denied.status_code == 403
