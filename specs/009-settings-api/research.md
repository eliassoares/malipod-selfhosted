# Research: Settings API

## Decision: Reuse the existing FastAPI app and HTTP Basic ownership helper for both settings endpoints

**Rationale**: The repository already exposes authenticated compatibility APIs
for subscriptions and episodes using the same FastAPI application and a shared
pattern that authenticates the caller and compares the requested username
against the authenticated account. Reusing that approach keeps settings access
control consistent and avoids creating a second authentication path just for
settings.

**Alternatives considered**:
- Session-cookie authentication for API settings endpoints: inconsistent with
  the existing compatibility API surface and less suitable for client sync.
- Duplicating ownership checks independently in each handler: simpler short
  term, but more likely to drift across scopes and endpoints.

## Decision: Store one JSON document per valid scope target instead of one row per setting key

**Rationale**: The API reads and writes whole settings objects, supports
arbitrary JSON values, and returns the full resulting document after each
mutation. A single JSON column per scope target matches that contract directly,
keeps updates simple, and avoids extra joins or per-key conflict logic that a
row-per-key schema would introduce.

**Alternatives considered**:
- One relational row per key-value pair: more flexible for ad hoc querying, but
  unnecessary for this API and more complex for nested JSON values.
- Opaque blob storage with no structured JSON column: less portable and weaker
  for validation and test assertions.

## Decision: Model settings persistence with four focused tables, one for each scope

**Rationale**: Account, device, podcast, and episode scopes point to different
domain entities with different integrity requirements. Four small tables with
clear foreign keys preserve relational integrity and keep lookups explicit,
while still sharing one service layer and one API contract. This is simpler and
safer than a polymorphic table that stores `scope_type` and `scope_id` without
real foreign-key enforcement.

**Alternatives considered**:
- One generic polymorphic settings table: fewer tables, but weaker foreign-key
  guarantees and more conditional logic in every query.
- Embedding settings JSON directly on existing user/device/feed/episode tables:
  couples unrelated write paths and makes future evolution of settings history
  or metadata harder.

## Decision: Treat missing settings documents as empty objects for valid targets, but missing scope targets as `404 Not Found`

**Rationale**: Clients should be able to read a valid scope before any settings
have been stored and receive an empty JSON object. That is different from
requesting a device, podcast, or episode target that does not exist for the
user, which should remain a true not-found error. This distinction keeps the
API predictable while preserving useful validation.

**Alternatives considered**:
- Return `404` whenever no settings row exists: forces clients to special-case
  empty state and conflates absence of data with absence of target.
- Auto-create all scope documents eagerly: adds unnecessary rows and migration
  complexity for targets that may never receive settings.

## Decision: Resolve podcast and episode scopes through existing `PodcastFeedModel` and `EpisodeModel`

**Rationale**: The repository already treats feed URLs and episode URLs as the
canonical podcast and episode identifiers in subscriptions and episodes
features. Reusing those same models prevents duplicate identity rules and
ensures settings attach to the same targets that other sync features already
understand.

**Alternatives considered**:
- Store raw podcast and episode URLs only inside settings rows: simpler schema,
  but duplicates canonical target identity and weakens referential integrity.
- Introduce new podcast or episode lookup tables just for settings: redundant
  with the existing domain model.

## Decision: Keep known settings as regular stored keys without adding new website-side behavior in this feature

**Rationale**: The request requires that documented keys such as
`public_profile`, `store_user_agent`, `public_subscriptions`,
`public_subscription`, and `is_favorite` be supported and retrievable. The
current scope is the compatibility API for storing and reading settings, not a
broader website privacy or favorites behavior overhaul. Persisting the keys
without new side effects keeps the implementation minimal and aligned with the
spec.

**Alternatives considered**:
- Implement website-side toggles immediately: larger scope than requested and
  harder to verify in one feature slice.
- Reject unknown keys and accept only documented settings: too restrictive for
  a sync API that explicitly allows arbitrary key-value pairs.

## Decision: Place the new SQLAlchemy tables in a dedicated `app/db/models/settings.py` module

**Rationale**: The settings feature crosses user, device, feed, and episode
domains. Grouping the four settings tables in one new model module keeps the
feature's persistence surface easy to review, reduces churn in already crowded
domain-model files, and makes the migration scope more obvious.

**Alternatives considered**:
- Add each settings table into the related existing model file: keeps targets
  nearby, but spreads one cohesive feature across multiple files.
- Create one service-only abstraction with raw SQL and no ORM models: less
  idiomatic for this repository and harder to validate with the current test
  patterns.
