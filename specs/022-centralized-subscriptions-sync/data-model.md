# Data Model: Centralized Subscriptions Sync

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/spec.md`
**Date**: 2026-04-24

## New Field (Persistence)

- **User.centralize_sync**: boolean flag indicating whether subscriptions reads and deltas should be centralized (union across devices).
  - Default: false
  - Scope: per user
  - Affects: read behavior only (GET subscriptions; POST delta changes)
  - Does not affect: writes (PUT remains device-scoped)

## Existing Entities Used

- **DeviceSubscription**: tracks subscribed feeds per device, with an “active” state (not unsubscribed).
- **SubscriptionChangeEvent**: records per-device subscribe/unsubscribe operations and timestamps for delta computations.
- **Device**: links a subscription/change event to a user via device ownership.

## Derived Views (No New Tables)

- **Centralized active subscriptions**: distinct feed URLs across all active device subscriptions for the user.
- **Centralized delta remove filter**: `remove` candidates from change events since `since`, filtered out if URL is still present in the centralized active subscriptions set.

## Constraints

- Centralized mode must not leak data across users; all queries must be constrained to the authenticated user.
- Centralized mode affects reads only; device identifier in the route remains for auth and compatibility.
