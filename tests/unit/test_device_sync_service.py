from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.schemas.auth import RegistrationInput
from app.schemas.device import DeviceUpsertRequest
from app.schemas.sync_devices import SyncDevicesMutation
from app.services.auth import AuthService
from app.services.devices import DeviceService
from app.services.sync_devices import SyncDevicesService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.config import Settings


def build_registration(nickname: str = "listener_1") -> RegistrationInput:
    return RegistrationInput(
        nickname=nickname,
        email=f"{nickname}@example.com",
        password="supersecret",
        password_confirmation="supersecret",
        picture_url="https://example.com/avatar.png",
        language_preference="en",
    )


@pytest.mark.asyncio
async def test_sync_status_sorts_groups_and_not_synced(
    db_session: AsyncSession, settings: Settings
) -> None:
    auth_service = AuthService(db_session, settings)
    user = await auth_service.create_user(build_registration())
    device_service = DeviceService(db_session)
    sync_service = SyncDevicesService(db_session)

    await device_service.upsert_device(
        user, DeviceUpsertRequest(device_id="pc-work", caption="pc", type="desktop")
    )
    await device_service.upsert_device(
        user, DeviceUpsertRequest(device_id="notebook", caption="nb", type="laptop")
    )
    await device_service.upsert_device(
        user, DeviceUpsertRequest(device_id="netbook", caption="nb2", type="laptop")
    )

    await sync_service.mutate(
        user,
        SyncDevicesMutation.model_validate(
            {"synchronize": [["notebook", "netbook"]], "stop-synchronize": []}
        ),
    )

    status = await sync_service.get_status(user)

    assert status.synchronized == [["netbook", "notebook"]]
    assert status.not_synchronized == ["pc-work"]


@pytest.mark.asyncio
async def test_sync_mutation_cleans_up_singleton_groups(
    db_session: AsyncSession, settings: Settings
) -> None:
    auth_service = AuthService(db_session, settings)
    user = await auth_service.create_user(build_registration())
    device_service = DeviceService(db_session)
    sync_service = SyncDevicesService(db_session)

    await device_service.upsert_device(
        user, DeviceUpsertRequest(device_id="notebook", caption="nb", type="laptop")
    )
    await device_service.upsert_device(
        user, DeviceUpsertRequest(device_id="netbook", caption="nb2", type="laptop")
    )

    await sync_service.mutate(
        user,
        SyncDevicesMutation.model_validate({"synchronize": [["notebook", "netbook"]]}),
    )
    await sync_service.mutate(
        user,
        SyncDevicesMutation.model_validate({"stop-synchronize": ["netbook"]}),
    )

    status = await sync_service.get_status(user)
    assert status.synchronized == []
    assert status.not_synchronized == ["netbook", "notebook"]
