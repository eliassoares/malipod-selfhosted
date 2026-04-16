from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegistrationInput
from app.schemas.device import DeviceUpsertRequest
from app.schemas.episode import EpisodeActionInput
from app.services.auth import AuthService
from app.services.devices import DeviceError, DeviceService
from app.services.episodes import EpisodeService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings
    from app.db.models.user import UserModel


def build_registration(
    nickname: str = "listener_1", email: str = "listener@example.com"
) -> RegistrationInput:
    return RegistrationInput(
        nickname=nickname,
        email=email,
        password="supersecret",
        password_confirmation="supersecret",
        picture_url="https://example.com/avatar.png",
        language_preference="en",
    )


@pytest.mark.parametrize("device_id", ["bad id", "emoji-😀", "slash/name", ""])
def test_device_upsert_request_rejects_invalid_device_id(device_id: str) -> None:
    with pytest.raises(ValidationError, match="device_id"):
        DeviceUpsertRequest(device_id=device_id, caption="Laptop", type="laptop")


def test_device_upsert_request_requires_supported_type() -> None:
    with pytest.raises(ValidationError, match="type"):
        DeviceUpsertRequest(device_id="workstation-1", caption="Desk", type="tablet")


@pytest.mark.asyncio
async def test_device_service_creates_and_updates_device(
    db_session: AsyncSession, settings: Settings
) -> None:
    auth_service = AuthService(db_session, settings)
    user = await auth_service.create_user(build_registration())
    service = DeviceService(db_session)

    created = await service.upsert_device(
        user,
        DeviceUpsertRequest(
            device_id="workstation-1",
            caption="Desk Machine",
            type="desktop",
        ),
    )

    assert created.device_id == "workstation-1"
    assert created.caption == "Desk Machine"
    assert created.device_type == "desktop"

    updated = await service.upsert_device(
        user,
        DeviceUpsertRequest(device_id="workstation-1", caption="Renamed Device"),
    )

    assert updated.caption == "Renamed Device"
    assert updated.device_type == "desktop"


@pytest.mark.asyncio
async def test_device_service_lists_devices_with_active_subscription_counts(
    db_session: AsyncSession, settings: Settings
) -> None:
    auth_service = AuthService(db_session, settings)
    user = await auth_service.create_user(build_registration())
    service = DeviceService(db_session)

    device = await service.upsert_device(
        user,
        DeviceUpsertRequest(
            device_id="phone-01",
            caption="Phone",
            type="mobile",
        ),
    )
    await service.replace_device_subscriptions(
        device,
        [
            {
                "url": "https://example.com/feed-1.xml",
                "title": "Feed One",
            },
            {
                "url": "https://example.com/feed-2.xml",
                "title": "Feed Two",
            },
        ],
    )

    summaries = await service.list_devices_for_user(user)

    assert len(summaries) == 1
    assert summaries[0].id == "phone-01"
    assert summaries[0].subscriptions == 2


async def create_user_pair(
    db_session: AsyncSession, settings: Settings
) -> tuple[UserModel, UserModel]:
    auth_service = AuthService(db_session, settings)
    owner = await auth_service.create_user(build_registration())
    other = await auth_service.create_user(
        build_registration(nickname="listener_2", email="listener2@example.com")
    )
    return owner, other


@pytest.mark.asyncio
async def test_device_service_rejects_foreign_device_lookup(
    db_session: AsyncSession, settings: Settings
) -> None:
    owner, other = await create_user_pair(db_session, settings)
    service = DeviceService(db_session)
    await service.upsert_device(
        owner,
        DeviceUpsertRequest(
            device_id="shared-name",
            caption="Owner Device",
            type="desktop",
        ),
    )

    with pytest.raises(DeviceError, match="device_not_found"):
        await service.get_device_for_user(other, "shared-name")


@pytest.mark.asyncio
async def test_device_service_returns_incremental_updates_with_optional_actions(
    db_session: AsyncSession, settings: Settings
) -> None:
    auth_service = AuthService(db_session, settings)
    user = await auth_service.create_user(build_registration())
    service = DeviceService(db_session)
    device = await service.upsert_device(
        user,
        DeviceUpsertRequest(
            device_id="sync-box",
            caption="Sync Box",
            type="server",
        ),
    )

    now = datetime.now(UTC)
    await service.replace_device_subscriptions(
        device,
        [
            {
                "url": "https://example.com/feed-current.xml",
                "title": "Current Feed",
                "description": "Current description",
            }
        ],
    )
    await service.record_episode_update(
        user=user,
        device=device,
        feed_url="https://example.com/feed-current.xml",
        feed_title="Current Feed",
        episode_url="https://example.com/episode-1.mp3",
        episode_title="Episode One",
        status="play",
        occurred_at=now,
        action={"position": 120, "started": True},
    )

    initial = await service.get_updates_for_device(user, "sync-box", None, True)

    assert initial.add[0].title == "Current Feed"
    assert initial.updates[0].status == "play"
    assert initial.updates[0].action == {"position": 120, "started": True}

    later = await service.record_episode_update(
        user=user,
        device=device,
        feed_url="https://example.com/feed-current.xml",
        feed_title="Current Feed",
        episode_url="https://example.com/episode-1.mp3",
        episode_title="Episode One",
        status="download",
        occurred_at=now + timedelta(seconds=30),
        action={"downloaded": True},
    )

    incremental = await service.get_updates_for_device(
        user,
        "sync-box",
        int(later.occurred_at.timestamp()) - 1,
        True,
    )

    assert len(incremental.updates) == 1
    assert incremental.updates[0].status == "download"
    assert incremental.updates[0].action == {"downloaded": True}


@pytest.mark.asyncio
async def test_device_updates_remain_compatible_with_episode_history_uploads(
    db_session: AsyncSession, settings: Settings
) -> None:
    auth_service = AuthService(db_session, settings)
    user = await auth_service.create_user(build_registration())
    device_service = DeviceService(db_session)
    episode_service = EpisodeService(db_session)
    device = await device_service.upsert_device(
        user,
        DeviceUpsertRequest(
            device_id="sync-box",
            caption="Sync Box",
            type="server",
        ),
    )

    upload = await episode_service.upload_actions(
        user,
        [
            EpisodeActionInput(
                podcast="https://example.com/feed-current.xml",
                episode="https://example.com/episode-1.mp3",
                device=device.device_id,
                action="play",
                started=20,
                position=180,
                total=600,
            )
        ],
    )
    updates = await device_service.get_updates_for_device(
        user,
        device.device_id,
        upload.timestamp - 1,
        True,
    )

    assert len(updates.updates) == 1
    assert updates.updates[0].status == "play"
    assert updates.updates[0].action == {
        "started": 20,
        "position": 180,
        "total": 600,
    }
