# Research: Centralized Subscriptions Sync

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/spec.md`
**Date**: 2026-04-24

## Decisions

### Decision: Centralized read semantics (GET subscriptions)

**Chosen**: When `centralize_sync` is enabled, return the distinct union of active subscription URLs across all devices of the user (not device-scoped). Apply the same behavior to both `.json` and `.opml`.

**Rationale**: Matches the desired “transparent” behavior without changing the endpoint shape, and keeps device-scoped writes intact.

**Alternatives considered**:
- Persisting a unified subscriptions table: rejected (adds new persistence/sync complexity).

### Decision: Centralized delta semantics (POST subscriptions delta)

**Chosen**:
- `add`: union of URLs added by any device since `since`.
- `remove`: include a URL only if it is not present in the current union of active subscriptions across all devices at read time.

**Rationale**: Prevents a single-device unsubscribe from removing a feed for other devices, while still allowing removal once the feed is actually absent everywhere.

**Alternatives considered**:
- Use only change events without checking current state: rejected (can incorrectly remove feeds still subscribed on another device).

### Decision: Write semantics (PUT subscriptions)

**Chosen**: Keep PUT device-scoped and unchanged.

**Rationale**: Maintains protocol expectations and avoids implicit writes across devices.

### Decision: UI toggle storage and privacy

**Chosen**: Store a boolean `users.centralize_sync` defaulting to false. Only the user can change their own setting via the profile UI.

**Rationale**: Simple, explicit, and easy to test; prevents cross-account leakage.
