from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from sqlalchemy import delete, func, select, update

from app.db.models.device import DeviceModel
from app.db.models.device_sync_group import DeviceSyncGroupModel
from app.schemas.sync_devices import SyncDevicesMutation, SyncDevicesStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models.user import UserModel


class SyncDevicesError(Exception):
    def __init__(
        self,
        code: Literal[
            "device_not_found",
            "invalid_device_id",
            "invalid_payload",
        ],
        *,
        detail: str | None = None,
    ) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail or code)


@dataclass(frozen=True, slots=True)
class _StatusGroups:
    synchronized: list[list[str]]
    not_synchronized: list[str]

    def to_schema(self) -> SyncDevicesStatus:
        return SyncDevicesStatus.model_validate(
            {
                "synchronized": self.synchronized,
                "not-synchronized": self.not_synchronized,
            }
        )


class SyncDevicesService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _cleanup_small_groups(self, *, user_id: int, group_ids: set[int]) -> None:
        if not group_ids:
            return

        ids = sorted(group_ids)

        # Single query: member count per group.
        result = await self.session.execute(
            select(DeviceModel.sync_group_id, func.count(DeviceModel.id))
            .where(
                DeviceModel.user_id == user_id,
                DeviceModel.sync_group_id.in_(ids),
            )
            .group_by(DeviceModel.sync_group_id)
        )
        counts: dict[int, int] = {row[0]: row[1] for row in result.all()}

        # Groups with fewer than 2 members (including groups already emptied).
        small = [gid for gid in ids if counts.get(gid, 0) < 2]
        if not small:
            return

        # Bulk-null singleton memberships, then bulk-delete the group rows.
        await self.session.execute(
            update(DeviceModel)
            .where(
                DeviceModel.user_id == user_id,
                DeviceModel.sync_group_id.in_(small),
            )
            .values(sync_group_id=None)
        )
        await self.session.execute(
            delete(DeviceSyncGroupModel).where(
                DeviceSyncGroupModel.user_id == user_id,
                DeviceSyncGroupModel.id.in_(small),
            )
        )

    async def get_status(self, user: UserModel) -> SyncDevicesStatus:
        result = await self.session.execute(
            select(DeviceModel.device_id, DeviceModel.sync_group_id)
            .where(DeviceModel.user_id == user.id)
            .order_by(DeviceModel.created_at.asc(), DeviceModel.id.asc())
        )
        rows: list[tuple[str, int | None]] = [(row[0], row[1]) for row in result.all()]
        if not rows:
            return _StatusGroups(synchronized=[], not_synchronized=[]).to_schema()

        by_group: dict[int, list[str]] = {}
        ungrouped: list[str] = []
        for device_id, sync_group_id in rows:
            if sync_group_id is None:
                ungrouped.append(device_id)
            else:
                by_group.setdefault(sync_group_id, []).append(device_id)

        synchronized: list[list[str]] = []
        not_synchronized: list[str] = []

        for group_devices in by_group.values():
            if len(group_devices) < 2:
                not_synchronized.extend(group_devices)
                continue
            synchronized.append(sorted(group_devices))

        not_synchronized.extend(ungrouped)
        not_synchronized = sorted(set(not_synchronized))
        synchronized = sorted(synchronized, key=lambda group: group[0])

        return _StatusGroups(
            synchronized=synchronized,
            not_synchronized=not_synchronized,
        ).to_schema()

    async def mutate(
        self,
        user: UserModel,
        payload: SyncDevicesMutation,
    ) -> SyncDevicesStatus:
        synchronize = payload.synchronize
        stop = payload.stop_synchronize

        referenced: set[str] = set()
        for group_devices in synchronize:
            referenced.update(group_devices)
        referenced.update(stop)

        # Fetch referenced devices; fail fast if any are missing (atomic semantics).
        result = await self.session.execute(
            select(DeviceModel).where(DeviceModel.user_id == user.id)
        )
        all_devices = result.scalars().all()
        if not all_devices:
            if referenced:
                raise SyncDevicesError(
                    "device_not_found",
                    detail="no devices registered for user",
                )
            return await self.get_status(user)

        devices_by_id: dict[str, DeviceModel] = {
            device.device_id: device for device in all_devices
        }
        missing = sorted(referenced - set(devices_by_id)) if referenced else []
        if missing:
            raise SyncDevicesError(
                "device_not_found",
                detail=f"missing devices: {', '.join(missing)}",
            )

        affected_group_ids: set[int] = set()
        try:
            # Apply synchronize mutations first, then stop mutations as an override.
            for requested_group in synchronize:
                closure_device_ids: set[str] = set(requested_group)
                seed_group_ids: set[int] = set()
                for device_id in requested_group:
                    group_id = devices_by_id[device_id].sync_group_id
                    if group_id is not None:
                        seed_group_ids.add(group_id)

                if seed_group_ids:
                    result = await self.session.execute(
                        select(DeviceModel.device_id).where(
                            DeviceModel.user_id == user.id,
                            DeviceModel.sync_group_id.in_(sorted(seed_group_ids)),
                        )
                    )
                    closure_device_ids.update(row[0] for row in result.all())

                closure_devices = [
                    devices_by_id[device_id] for device_id in closure_device_ids
                ]
                closure_group_ids: set[int] = {
                    device.sync_group_id
                    for device in closure_devices
                    if device.sync_group_id is not None
                }
                affected_group_ids.update(closure_group_ids)

                target_group_id: int
                if closure_group_ids:
                    target_group_id = min(closure_group_ids)
                else:
                    new_group = DeviceSyncGroupModel(user_id=user.id)
                    self.session.add(new_group)
                    await self.session.flush()
                    target_group_id = new_group.id

                affected_group_ids.add(target_group_id)

                for device in closure_devices:
                    device.sync_group_id = target_group_id

                # Delete any merged-away groups (membership is already reassigned).
                merged_away = sorted(
                    group_id
                    for group_id in closure_group_ids
                    if group_id != target_group_id
                )
                if merged_away:
                    await self.session.execute(
                        delete(DeviceSyncGroupModel).where(
                            DeviceSyncGroupModel.user_id == user.id,
                            DeviceSyncGroupModel.id.in_(merged_away),
                        )
                    )
                    affected_group_ids.update(merged_away)

            # Apply stop-synchronize requests last to ensure explicit removals win.
            for device_id in stop:
                device = devices_by_id[device_id]
                if device.sync_group_id is not None:
                    affected_group_ids.add(device.sync_group_id)
                device.sync_group_id = None

            await self.session.flush()
            await self._cleanup_small_groups(
                user_id=user.id,
                group_ids=affected_group_ids,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return await self.get_status(user)
