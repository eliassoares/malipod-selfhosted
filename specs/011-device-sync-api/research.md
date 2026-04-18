# Research: Device Synchronization API

## Decision: Reuse existing authentication and ownership enforcement for sync-devices

**Rationale**: The repository already exposes authenticated `/api/2` endpoints
that authenticate the caller and enforce that the requested `username` matches
the authenticated account (via `authenticate_api_user`). Reusing this pattern
keeps cross-account protections consistent and reduces the risk of leaking sync
state between users.

**Alternatives considered**:
- Endpoint-local custom authorization: duplicates existing behavior and increases
  the chance of subtle inconsistencies.
- Making this endpoint public/read-only without auth: violates the contract
  requirement and exposes private device metadata.

## Decision: Represent synchronization groups with a per-device `sync_group_id` plus a `device_sync_groups` table

**Rationale**: The core business concept is “connected components” of devices
that should share state. Persisting a `sync_group_id` directly on each device is
the simplest model for queries and updates. A separate `device_sync_groups` table
keeps group identity explicit and allows cleaning up empty groups cleanly.

**Alternatives considered**:
- Membership join table (`device_sync_group_members`): flexible, but adds more
  joins and complexity than required for the current contract.
- Storing group membership as a JSON array on the user: harder to enforce
  ownership/uniqueness and less friendly for SQL updates and test seeding.

## Decision: Treat groups with fewer than 2 devices as “not synchronized”

**Rationale**: A single device in a “group” is not meaningfully synchronized with
anything. Treating it as not synchronized simplifies responses and matches the
feature assumptions/edge cases defined in the spec.

**Alternatives considered**:
- Returning singleton groups inside `synchronized`: confusing for clients and
  conflicts with the intention that `synchronized` represents mutual sync.

## Decision: POST mutations are atomic and idempotent

**Rationale**: The endpoint may be called repeatedly by clients. Atomic behavior
prevents partial application when a request references unknown devices or devices
from a different user. Idempotency ensures clients can safely retry without
accidentally changing group structure in unexpected ways.

**Alternatives considered**:
- Partial-apply semantics (“best effort”): increases client-side complexity and
  creates hard-to-debug drift between devices.

## Decision: Deterministic response ordering for stability across PostgreSQL and SQLite

**Rationale**: Contract tests and clients benefit from stable ordering. The API
will emit device IDs sorted within each group, and groups will be ordered by the
first device ID in each group, with `not-synchronized` also sorted.

**Alternatives considered**:
- Natural database order: nondeterministic across engines and query plans.

## Decision: Scope stays within device grouping only

**Rationale**: The contract defines only status and grouping mutations. Keeping
this feature focused avoids coupling to episodes/subscriptions settings logic and
keeps the surface minimal and reviewable.

**Alternatives considered**:
- Extending this endpoint to also trigger data sync or propagate subscriptions:
  expands beyond the requested compatibility surface.
