# Research: Episodes API

## Decision: Reuse the existing FastAPI app and HTTP Basic ownership helper for episode actions

**Rationale**: The repository already exposes compatibility-style authenticated
API routes and has a tested helper pattern for authenticating the requested
username with HTTP Basic credentials. Reusing the same application, dependency
injection, and ownership enforcement keeps the episode-actions surface aligned
with devices and subscriptions and avoids duplicating security logic.

**Alternatives considered**:
- Separate sync microservice: would create unnecessary operational and testing
  complexity for a feature that shares the same persistence and auth context.
- Endpoint-local auth handling only: would duplicate logic and increase the risk
  of cross-account leakage.

## Decision: Add append-only episode action history instead of overloading the current latest-state table

**Rationale**: The existing `EpisodeActionModel` has a uniqueness constraint on
`(user_id, episode_id)`, which is appropriate for the latest known state but
cannot store multiple uploads for the same episode over time. The episodes API
needs full retrieval since a server-issued timestamp plus optional aggregation
to the latest action. A separate append-only history entity satisfies that need
while preserving the current latest-state projection used elsewhere.

**Alternatives considered**:
- Remove the uniqueness constraint from `EpisodeActionModel`: would blur the
  meaning of the current table and risk breaking the device updates endpoint.
- Store only the latest event and skip history: would make `since` retrieval
  and unaggregated downloads impossible.

## Decision: Update the latest-state projection whenever a valid action event is appended

**Rationale**: Existing sync code already expects a one-row-per-user-per-episode
latest-state representation. Updating that projection as part of each upload
keeps the new history model and the current device updates logic coherent
without forcing a broader refactor now.

**Alternatives considered**:
- Recompute latest state from history on every read: simpler schema, but more
  query complexity and unnecessary recomputation for a path the app already
  supports.
- Drop the latest-state projection entirely: larger refactor than this feature
  requires and risks breaking already implemented behavior.

## Decision: Sanitize podcast and episode URLs by trimming whitespace, requiring ASCII, and accepting only `http`/`https`

**Rationale**: The supplied contract explicitly says URLs containing non-ASCII
characters or unsupported schemes are rewritten to the empty string and ignored
semantically. A small sanitizer that trims whitespace, enforces ASCII-only
content, and accepts only `http` or `https` meets the compatibility
expectation while remaining easy to test and explain.

**Alternatives considered**:
- Reuse the current subscription sanitizer unchanged: insufficient because the
  episodes spec adds the non-ASCII rejection rule.
- Aggressive URL canonicalization: risks changing semantics more than the
  contract requires in this increment.

## Decision: Require `started`, `position`, and `total` together only for `play` actions

**Rationale**: The contract explicitly says playback progress fields are valid
only for `play` and that all three values are required together. Treating the
triplet as one validation rule prevents partial progress payloads from becoming
ambiguous for receiving clients.

**Alternatives considered**:
- Allow partial progress fields: simpler for lenient uploads, but ambiguous for
  cross-device resume behavior and contrary to the documented contract.
- Require progress fields for all action types: unnecessary restriction for
  non-play events.

## Decision: Implement `aggregated=true` as latest matching history event per episode after filters are applied

**Rationale**: Aggregation is a retrieval concern, not a storage concern.
Applying `podcast`, `device`, and `since` filters first and then selecting the
latest remaining event for each episode matches the expectation that
aggregation collapses the matching result set rather than changing what is
considered eligible for the query.

**Alternatives considered**:
- Aggregate before applying filters: could return actions that do not match the
  requested device or timestamp window.
- Materialize a separate aggregated table: unnecessary extra persistence for
  this scope.

## Decision: Allow unknown device IDs in uploads and retrieval filters without requiring device registration

**Rationale**: The feature spec explicitly allows a device ID to be sent for
logging purposes and assumes a client may filter by that device later. Requiring
an existing device record would add avoidable coupling to the device-management
feature and block legitimate episode-action sync.

**Alternatives considered**:
- Require devices to exist before actions can mention them: stricter model, but
  not supported by the contract and harder for lightweight clients.
- Ignore device IDs entirely: would lose filtering value promised by the API.
