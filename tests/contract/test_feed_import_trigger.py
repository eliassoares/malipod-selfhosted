from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, patch

import pytest

from app.api.deps import get_runtime_settings
from tests.contract.test_subscriptions_api import register_user, seed_subscription_state
from tests.contract.test_user_data_tools_site import api_login

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.core.config import Settings


@pytest.fixture
def non_test_client(client: TestClient, settings: Settings) -> Iterator[TestClient]:
    """Client with environment='local' so background tasks are dispatched."""
    app = cast("FastAPI", client.app)
    non_test_settings = settings.model_copy(update={"environment": "local"})
    app.dependency_overrides[get_runtime_settings] = lambda: non_test_settings
    yield client
    app.dependency_overrides.pop(get_runtime_settings, None)


# ---------------------------------------------------------------------------
# POST /api/2/subscriptions — delta sync (AntennaPod and other clients)
# ---------------------------------------------------------------------------


def test_post_subscription_changes_triggers_import_for_added_url(
    non_test_client: TestClient, settings: Settings
) -> None:
    register_user(non_test_client)
    seed_subscription_state(settings)

    with patch(
        "app.api.routes.subscriptions_api.import_feed_in_background",
        new_callable=AsyncMock,
    ) as mock_import:
        non_test_client.post(
            "/api/2/subscriptions/listener_1/phone-01.json",
            auth=("listener_1", "supersecret"),
            json={"add": ["https://example.com/new.xml"], "remove": []},
        )

    mock_import.assert_called_once()
    _, call_url = mock_import.call_args.args
    assert call_url == "https://example.com/new.xml"


def test_post_subscription_changes_triggers_import_for_each_added_url(
    non_test_client: TestClient, settings: Settings
) -> None:
    register_user(non_test_client)
    seed_subscription_state(settings)

    with patch(
        "app.api.routes.subscriptions_api.import_feed_in_background",
        new_callable=AsyncMock,
    ) as mock_import:
        non_test_client.post(
            "/api/2/subscriptions/listener_1/phone-01.json",
            auth=("listener_1", "supersecret"),
            json={
                "add": [
                    "https://example.com/feed-x.xml",
                    "https://example.com/feed-y.xml",
                ],
                "remove": [],
            },
        )

    assert mock_import.call_count == 2
    called_urls = {call.args[1] for call in mock_import.call_args_list}
    assert called_urls == {
        "https://example.com/feed-x.xml",
        "https://example.com/feed-y.xml",
    }


def test_post_subscription_changes_no_import_when_only_removing(
    non_test_client: TestClient, settings: Settings
) -> None:
    register_user(non_test_client)
    seed_subscription_state(settings)

    with patch(
        "app.api.routes.subscriptions_api.import_feed_in_background",
        new_callable=AsyncMock,
    ) as mock_import:
        non_test_client.post(
            "/api/2/subscriptions/listener_1/phone-01.json",
            auth=("listener_1", "supersecret"),
            json={"add": [], "remove": ["https://example.com/feed-a.xml"]},
        )

    mock_import.assert_not_called()


# ---------------------------------------------------------------------------
# PUT /subscriptions — full device upload
# ---------------------------------------------------------------------------


def test_put_device_subscriptions_triggers_import_for_each_url(
    non_test_client: TestClient,
) -> None:
    register_user(non_test_client)

    with patch(
        "app.api.routes.subscriptions_api.import_feed_in_background",
        new_callable=AsyncMock,
    ) as mock_import:
        non_test_client.put(
            "/subscriptions/listener_1/my-device.txt",
            auth=("listener_1", "supersecret"),
            content="https://example.com/feed-a.xml\nhttps://example.com/feed-b.xml\n",
            headers={"Content-Type": "text/plain"},
        )

    assert mock_import.call_count == 2
    called_urls = {call.args[1] for call in mock_import.call_args_list}
    assert called_urls == {
        "https://example.com/feed-a.xml",
        "https://example.com/feed-b.xml",
    }


def test_put_device_subscriptions_empty_list_triggers_no_import(
    non_test_client: TestClient,
) -> None:
    register_user(non_test_client)

    with patch(
        "app.api.routes.subscriptions_api.import_feed_in_background",
        new_callable=AsyncMock,
    ) as mock_import:
        non_test_client.put(
            "/subscriptions/listener_1/my-device.txt",
            auth=("listener_1", "supersecret"),
            content="",
            headers={"Content-Type": "text/plain"},
        )

    mock_import.assert_not_called()


# ---------------------------------------------------------------------------
# POST /user/profile/{nickname}/import — snapshot data import
# ---------------------------------------------------------------------------


def test_import_snapshot_triggers_feed_import_for_subscribed_feeds(
    non_test_client: TestClient,
) -> None:
    register_user(non_test_client)
    api_login(non_test_client)

    export = non_test_client.post("/user/profile/listener_1/export").json()
    export["device_subscriptions"] = [
        {
            "device_id": "phone",
            "feed_url": "https://example.com/podcast.xml",
            "subscribed_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
    ]

    with patch(
        "app.api.routes.profile_site.import_feed_in_background",
        new_callable=AsyncMock,
    ) as mock_import:
        non_test_client.post(
            "/user/profile/listener_1/import",
            files={
                "snapshot_file": (
                    "snapshot.json",
                    json.dumps(export),
                    "application/json",
                )
            },
            follow_redirects=False,
        )

    mock_import.assert_called_once()
    _, call_url = mock_import.call_args.args
    assert call_url == "https://example.com/podcast.xml"
