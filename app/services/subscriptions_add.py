from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.schemas.device import DeviceUpsertRequest

if TYPE_CHECKING:
    from app.db.models.user import UserModel
    from app.services.devices import DeviceService
    from app.services.subscriptions import SubscriptionService


@dataclass(slots=True)
class SubscriptionAddService:
    device_service: DeviceService
    subscription_service: SubscriptionService

    async def subscribe_user_to_feed(self, user: UserModel, feed_url: str) -> None:
        await self.device_service.upsert_device(
            user, DeviceUpsertRequest(device_id="web", caption="Web", type="other")
        )
        devices = await self.device_service.list_devices_for_user(user)
        for device in devices:
            await self.subscription_service.apply_delta(user, device.id, [feed_url], [])
