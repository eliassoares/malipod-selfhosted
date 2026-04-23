from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.schemas.device import DeviceUpsertRequest

if TYPE_CHECKING:
    from app.db.models.user import UserModel
    from app.services.devices import DeviceService
    from app.services.subscriptions import SubscriptionService

_WEB_DEVICE = DeviceUpsertRequest(device_id="web", caption="Web", type="other")


@dataclass(slots=True)
class SubscriptionAddService:
    device_service: DeviceService
    subscription_service: SubscriptionService

    async def _ensure_devices(self, user: UserModel) -> list[str]:
        devices = await self.device_service.list_devices_for_user(user)
        if devices:
            return [d.id for d in devices]
        await self.device_service.upsert_device(user, _WEB_DEVICE)
        return ["web"]

    async def subscribe_user_to_feed(self, user: UserModel, feed_url: str) -> None:
        for device_id in await self._ensure_devices(user):
            await self.subscription_service.apply_delta(user, device_id, [feed_url], [])

    async def unsubscribe_user_from_feed(self, user: UserModel, feed_url: str) -> None:
        devices = await self.device_service.list_devices_for_user(user)
        for device in devices:
            await self.subscription_service.apply_delta(user, device.id, [], [feed_url])
