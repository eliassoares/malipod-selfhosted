# Data Model: Device Synchronization API

## Overview

This feature adds per-user device synchronization grouping. A “synchronization
group” is a set of two or more devices owned by the same user that should be
treated as mutually synchronized by compatible clients.

The API surfaces the grouping as:

- `synchronized`: list of device-ID lists, each list representing one group
- `not-synchronized`: list of device IDs that are not in any group

## Entity: DeviceSyncGroup

**Purpose**: Represents one per-user synchronization group identifier.

**Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `created_at`: first persistence time
- `updated_at`: latest persistence refresh time

**Validation Rules**:
- A group belongs to exactly one user.
- Groups are deleted when they become empty (no member devices).

**Relationships**:
- Has many `Device` rows (membership is represented by a device pointing at the
  group identifier).

## Entity: Device (extended)

**Purpose**: Represents a registered client device owned by one user. This
feature extends devices with optional group membership.

**New/Relevant Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `device_id`: user-scoped unique external identifier
- `sync_group_id`: optional reference to `DeviceSyncGroup` (nullable)
- `created_at`, `updated_at`: timestamps already used by other device flows

**Validation Rules**:
- `(user_id, device_id)` remains unique.
- `sync_group_id` is nullable; null means “not synchronized”.
- A device can only reference a group owned by the same `user_id` (enforced via
  application logic and, when feasible, a composite foreign key).

**Relationships**:
- Belongs to one `User`
- Optionally belongs to one `DeviceSyncGroup`

## Entity: SyncDevicesStatus (API projection)

**Purpose**: Represents the serialized response body for both GET and POST.

**Fields**:
- `synchronized`: list of lists of device IDs
- `not-synchronized`: list of device IDs

**Validation Rules**:
- Device IDs in output must all belong to the targeted user.
- Each device appears in exactly one place: either in one `synchronized` group
  or in `not-synchronized`.
- Groups with fewer than 2 devices are treated as not synchronized (i.e., they
  do not appear in `synchronized`).
- Response ordering is deterministic:
  - device IDs sorted within a group
  - groups sorted by their first device ID
  - `not-synchronized` sorted

## State Transitions

### Group Membership Lifecycle

- `not synchronized` -> `synchronized`: A POST `synchronize` request assigns the
  devices (and any devices already in their groups) to one shared group.
- `synchronized` -> `not synchronized`: A POST `stop-synchronize` request removes
  a device from its group.
- `group cleanup`: After removals, if a group has fewer than 2 member devices,
  remaining devices are moved to `not synchronized` and the group is deleted.

## Persistence Notes

- A new `device_sync_groups` table stores per-user group identifiers.
- The `devices` table receives a nullable `sync_group_id` reference.
- Group merges are modeled by updating affected devices to a shared
  `sync_group_id` and deleting any now-empty groups.
- Requests are validated before mutation; if any referenced device is missing or
  belongs to another user, the mutation is rejected with no partial updates.

## Future Extension Notes

This model leaves room for:

- richer group metadata (e.g., a human label) without changing membership rules
- additional sync endpoints that operate “per group” rather than “per device”
  while keeping the same group identity
