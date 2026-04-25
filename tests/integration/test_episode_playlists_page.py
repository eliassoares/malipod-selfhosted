from __future__ import annotations

from typing import TYPE_CHECKING

from tests.contract.test_home_page import api_login, register_user

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_playlists_manage_page_requires_login(client: TestClient) -> None:
    response = client.get("/user/listener_1/playlists", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_playlists_manage_page_renders_and_lists_favorites(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get("/user/listener_1/playlists")

    assert response.status_code == 200
    assert "/user/listener_1/playlists/create" in response.text
    assert "Favorites" in response.text


def test_playlists_create_update_delete_and_owner_only(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    register_user(client, nickname="listener_2")
    api_login(client, nickname="listener_1")

    created = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "My Playlist", "description": "hello"},
        follow_redirects=False,
    )
    assert created.status_code == 303
    assert "success=created" in created.headers["location"]

    playlist_id = int(
        created.headers["location"].split("playlist_id=")[-1].split("&")[0]
    )

    updated = client.post(
        f"/user/listener_1/playlists/{playlist_id}/update",
        data={"title": "My Playlist 2", "description": "changed"},
        follow_redirects=False,
    )
    assert updated.status_code == 303
    assert "success=updated" in updated.headers["location"]

    forbidden = client.post(
        "/user/listener_2/playlists/create",
        data={"title": "Nope", "description": "x"},
        follow_redirects=False,
    )
    assert forbidden.status_code == 404

    deleted = client.post(
        f"/user/listener_1/playlists/{playlist_id}/delete",
        data={"confirm": "1"},
        follow_redirects=False,
    )
    assert deleted.status_code == 303
    assert "success=deleted" in deleted.headers["location"]


def test_playlists_reject_description_over_limit_and_large_image(
    client: TestClient,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    too_long = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "My Playlist", "description": "x" * 1025},
        follow_redirects=False,
    )
    assert too_long.status_code == 303
    assert "error=invalid_description" in too_long.headers["location"]

    big_bytes = b"\x89PNG\r\n\x1a\n" + b"a" * (1024 * 1024)
    too_big = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "My Playlist", "description": "ok"},
        files={"image": ("cover.png", big_bytes, "image/png")},
        follow_redirects=False,
    )
    assert too_big.status_code == 303
    assert "error=image_too_large" in too_big.headers["location"]


def test_update_playlist_without_new_image_preserves_existing_image(
    client: TestClient,
) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    # Create with a valid PNG image
    png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    created = client.post(
        "/user/listener_1/playlists/create",
        data={"title": "ImgPlaylist", "description": ""},
        files={"image": ("cover.png", png_header, "image/png")},
        follow_redirects=False,
    )
    assert created.status_code == 303
    playlist_id = int(
        created.headers["location"].split("playlist_id=")[-1].split("&")[0]
    )

    # Check image was stored
    detail = client.get(f"/user/listener_1/playlists/{playlist_id}")
    assert "uploads/playlists" in detail.text

    # Update title only (no new image)
    updated = client.post(
        f"/user/listener_1/playlists/{playlist_id}/update",
        data={"title": "ImgPlaylist Updated", "description": ""},
        follow_redirects=False,
    )
    assert updated.status_code == 303

    # Image URL must still be present after title-only update
    detail_after = client.get(f"/user/listener_1/playlists/{playlist_id}")
    assert "uploads/playlists" in detail_after.text


def test_playlist_detail_requires_owner(client: TestClient) -> None:
    register_user(client, nickname="playlist_owner")
    register_user(client, nickname="playlist_other")
    api_login(client, nickname="playlist_owner")

    created = client.post(
        "/user/playlist_owner/playlists/create",
        data={"title": "Private", "description": ""},
        follow_redirects=False,
    )
    playlist_id = int(
        created.headers["location"].split("playlist_id=")[-1].split("&")[0]
    )

    # Switch to other user
    client.post("/api/2/auth/playlist_owner/logout.json")
    api_login(client, nickname="playlist_other")

    # Detail page of another user's playlist returns 404
    response = client.get(
        f"/user/playlist_owner/playlists/{playlist_id}", follow_redirects=False
    )
    assert response.status_code in {303, 404}

    # Cannot delete another user's playlist
    deleted = client.post(
        f"/user/playlist_owner/playlists/{playlist_id}/delete",
        data={"confirm": "1"},
        follow_redirects=False,
    )
    assert deleted.status_code == 404


def test_unknown_error_param_is_ignored(client: TestClient) -> None:
    register_user(client, nickname="listener_1")
    api_login(client, nickname="listener_1")

    response = client.get("/user/listener_1/playlists?error=<script>alert(1)</script>")
    assert response.status_code == 200
    assert "alert(1)" not in response.text
