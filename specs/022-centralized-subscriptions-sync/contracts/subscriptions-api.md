# Contracts: Subscriptions API (Centralized Sync)

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/spec.md`
**Date**: 2026-04-24

## Read subscriptions

### `GET /api/2/subscriptions/{username}/{device}.json`

- **Auth**: required (existing behavior)
- **When `centralize_sync` is false**: return active subscriptions for the requested device only.
- **When `centralize_sync` is true**: return distinct union of active subscriptions across all devices owned by the user.
- **Output shape**: unchanged.

### `GET /api/2/subscriptions/{username}/{device}.opml`

Same semantics as `.json` for selection of feeds; OPML output shape unchanged.

## Delta changes

### `POST /api/2/subscriptions/{username}/{device}.json?since=...`

- **Auth**: required (existing behavior)
- **When `centralize_sync` is false**: delta changes are scoped to the requested device (existing behavior).
- **When `centralize_sync` is true**:
  - `add`: a feed URL is included if it was added on any device since `since`.
  - `remove`: a feed URL is included only if it is absent from the current union of active subscriptions across all devices at read time.
- **Output shape**: unchanged.

## Writes

### `PUT /api/2/subscriptions/{username}/{device}.json`

No change: writes remain device-scoped and do not depend on `centralize_sync`.
