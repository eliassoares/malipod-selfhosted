# Research: Subscriptions API

## Decision: Reuse the existing FastAPI app and device-auth helpers for all subscriptions contracts

**Rationale**: The repository already exposes compatibility-style authenticated
routes under FastAPI and has working ownership enforcement for the device API.
Reusing the same application, dependency injection, and HTTP Basic
authentication helper keeps the security boundary in one place and prevents the
subscriptions feature from diverging into a separate service too early.

**Alternatives considered**:
- Separate sync microservice: would create unnecessary operational and testing
  complexity for a feature that shares the same persistence and auth context.
- Reimplement auth checks inside each route: simpler short term, but duplicates
  logic and increases the chance of cross-account leakage.

## Decision: Represent delta timestamps with an auto-incrementing subscription change-history table

**Rationale**: The API requires a server-issued timestamp/ID that clients can
pass back as `since`. A dedicated change-history table with monotonically
increasing integer IDs is the smallest design that provides deterministic delta
queries, works in PostgreSQL and SQLite tests, and avoids clock-resolution edge
cases from timestamp-only filtering.

**Alternatives considered**:
- Use wall-clock timestamps only: vulnerable to equal-time collisions and more
  awkward for deterministic tests.
- Store a single snapshot revision on the device row: insufficient because the
  API must return which URLs were added or removed after a prior sync point.

## Decision: Record add/remove events for both delta uploads and full-device replacements

**Rationale**: Full uploads are allowed to replace the complete device state,
and later delta reads should still reflect the net changes since the last known
timestamp. Emitting change-history rows during full replacement keeps the device
state and sync history aligned without inventing a second reconciliation path.

**Alternatives considered**:
- Treat full upload as state-only and skip history: later `since` reads would
  miss changes introduced by replacement and break client synchronization.
- Rebuild history lazily from snapshots: more complex and harder to reason
  about than appending explicit events at write time.

## Decision: Implement OPML, JSON, and plaintext parsing/rendering with standard-library helpers only

**Rationale**: The contracts need only simple feed URL exchange plus a small
amount of optional metadata for OPML and JSON reads. Python's standard library
already provides JSON handling and XML support sufficient for a minimal OPML
reader/writer, so the feature can stay dependency-free and satisfy the
project's simplicity goals.

**Alternatives considered**:
- Add a dedicated OPML library: could reduce some boilerplate, but adds runtime
  dependency surface for a narrow format requirement.
- Support only JSON initially: would not satisfy the required compatibility
  contract for OPML and plaintext.

## Decision: Restrict JSONP to JSON read endpoints only

**Rationale**: JSONP is meaningful only when the response body is JSON and the
client wants a callback wrapper. Applying it to OPML, plaintext, or upload
routes would either distort the expected media type or complicate parsing with
little compatibility value. Limiting JSONP to JSON reads matches the spec's
assumption that it is available only where the chosen output format supports it.

**Alternatives considered**:
- Allow JSONP for every read format: semantically incorrect for text/plain and
  XML outputs.
- Omit JSONP entirely: simpler, but misses the requested compatibility behavior.

## Decision: Sanitize feed URLs by trimming whitespace and accepting only `http`/`https`

**Rationale**: The supplied contract explicitly says unsupported URLs are
rewritten to the empty string and ignored semantically. A small sanitizer that
trims leading/trailing whitespace, normalizes blank results, and only accepts
`http` or `https` preserves the documented behavior while remaining easy to test
and explain.

**Alternatives considered**:
- Preserve all schemes and defer validation: would violate the required rewrite
  behavior and make downstream sync less predictable.
- Perform aggressive URL canonicalization beyond trimming and scheme checks:
  risks changing semantics more than the contract requires in this increment.

## Decision: Export deterministic, de-duplicated reads ordered by active subscription chronology and feed URL

**Rationale**: Clients need stable output to reconcile local state. For
device-level reads, ordering active subscriptions by `subscribed_at` then
`feed_url` yields predictable output without inventing user-facing sort
preferences. For account-wide reads, using the earliest active subscription time
per feed across the user's devices plus `feed_url` as a tie-breaker creates a
stable de-duplicated union.

**Alternatives considered**:
- Database natural row order: nondeterministic and brittle across engines.
- Alphabetical only: predictable, but discards useful chronology already present
  in the persisted model.
