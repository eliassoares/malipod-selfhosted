from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models.user import UserModel
    from app.services.devices import DeviceService
    from app.services.subscriptions import SubscriptionService


@dataclass(slots=True)
class SubscriptionAddService:
    device_service: DeviceService
    subscription_service: SubscriptionService

    async def subscribe_user_to_feed(self, user: UserModel, feed_url: str) -> None:
        devices = await self.device_service.list_devices_for_user(user)
        for device in devices:
            await self.subscription_service.apply_delta(user, device.id, [feed_url], [])

    async def unsubscribe_user_from_feed(self, user: UserModel, feed_url: str) -> None:
        devices = await self.device_service.list_devices_for_user(user)
        for device in devices:
            await self.subscription_service.apply_delta(user, device.id, [], [feed_url])
