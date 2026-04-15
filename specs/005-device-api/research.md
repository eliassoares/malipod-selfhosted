# Research: Device API

## Decision: Keep the Device API inside the existing FastAPI application

**Rationale**: The current project already serves authenticated JSON contracts
from one FastAPI runtime and shares auth/session dependencies through
`app/api/deps.py`. Extending that same application with device routes preserves
one authentication boundary, one configuration model, one database session
pattern, and one test harness.

**Alternatives considered**:
- Separate sync microservice: clearer long-term service boundaries, but too much
  operational and architectural overhead for the first device increment.
- Standalone worker-backed sync API: useful later for heavy change processing,
  but unnecessary for the requested CRUD-plus-sync contract.

## Decision: Persist devices as per-user records with a composite uniqueness rule

**Rationale**: The spec explicitly allows the same device ID string to exist in
different user accounts while requiring uniqueness within one account. The
simplest compliant persistence model is a `devices` table keyed by user plus
device ID, with caption/type stored directly on the device row and standard
created/updated timestamps.

**Alternatives considered**:
- Global unique device IDs: simpler lookup, but violates the supplied behavior
  and forces cross-account coordination on client-generated IDs.
- Stateless devices derived only from request paths: too weak for listing,
  subscription counts, and update ownership checks.

## Decision: Use a normalized sync model instead of a separate device change queue

**Rationale**: The feature needs add/remove subscription changes, episode
updates, and repeatable `since` filtering. A small normalized model centered on
devices, feeds, device subscriptions, episodes, and latest episode actions
supports those responses while staying aligned with future sync work. This keeps
the data inspectable and avoids adding a second persistence mechanism just for
change snapshots.

**Alternatives considered**:
- Append-only per-device change queue only: simpler first query path, but
  duplicates source-of-truth data and complicates reconciliation.
- On-the-fly response synthesis from no persisted domain model: too brittle for
  timestamps, subscription counts, and repeatable incremental syncs.

## Decision: Treat the `since` parameter as a UTC Unix timestamp in seconds

**Rationale**: The contract documents `since` as a timestamp without prescribing
  a richer format. Using UTC Unix seconds is easy to generate, stable across
  languages, compact in URLs, and straightforward to compare against persisted
  change timestamps in both PostgreSQL and SQLite-backed tests.

**Alternatives considered**:
- ISO 8601 timestamps in the query string: human-readable, but not the most
  compatible choice for this legacy-style contract.
- Database-specific sequence numbers: fast internally, but less portable and not
  obviously compatible with the external contract wording.

## Decision: Derive the device subscription count from active device-feed links

**Rationale**: The list-devices response must include a subscription count, but
the count is a read model rather than core device state. Computing it from
active device-subscription associations avoids denormalized counters that would
need extra maintenance logic on every change.

**Alternatives considered**:
- Persist a counter column on the device row: cheap to read, but risks drift and
  adds write-path complexity.
- Omit the count until later: incompatible with the requested contract.

## Decision: Reuse the existing authentication session and ownership dependency path

**Rationale**: The auth feature already authenticates users via session cookies
and API compatibility flows. Reusing that identity source means device routes can
authorize by comparing the authenticated user to the path `username` and do not
need a second credential model or extra API key management.

**Alternatives considered**:
- New device token scheme: potentially useful later, but outside this feature's
  scope.
- Anonymous device registration: incompatible with the requirement for HTTP
  authentication and unsafe for account-scoped data.

## Decision: Model episode update payloads around the latest known state per episode

**Rationale**: The updates response is interested in the current sync-relevant
view of an episode, not a full historical event log. Storing canonical episode
metadata plus the latest user action/state per episode allows the API to return
the required payload, and `include_actions=true` can attach the latest action
details only when the episode state is not `new`.

**Alternatives considered**:
- Return only raw action events: too noisy and not aligned with the requested
  `updates` response shape.
- Build updates from opaque serialized blobs: simpler persistence at first, but
  weak for querying, validation, and future sync evolution.
