# Research: Podcast Lists API

## Decision: Reuse the existing FastAPI app and HTTP Basic ownership helper for all list write endpoints

**Rationale**: The repository already exposes authenticated compatibility-style
routes for devices, subscriptions, and episodes using the same FastAPI
application and a shared ownership check based on HTTP Basic credentials.
Reusing that pattern keeps cross-account authorization logic consistent and
avoids inventing a separate publishing or website-only service for list
management.

**Alternatives considered**:
- Separate list-publishing service: would add operational and testing overhead
  for a feature that shares the same auth and persistence context.
- Duplicate auth checks inside each route: simpler short term, but increases the
  risk of inconsistent forbidden behavior across endpoints.

## Decision: Represent podcast lists with a dedicated list table plus an ordered join table to podcast feeds

**Rationale**: The feature needs user ownership, a stable canonical name, a
 human-readable title, and an ordered set of podcast references that can be
 rendered in multiple formats. A `podcast_lists` table plus `podcast_list_items`
 offers the smallest relational model that preserves list order, prevents
 duplicate membership within the same list, and reuses the existing
 `podcast_feeds` catalog rather than storing raw list blobs.

**Alternatives considered**:
- Store the uploaded document as an opaque text blob: simpler persistence, but
  makes format conversion, duplicate handling, and stable entry ordering harder.
- Add a separate feed snapshot table per list: unnecessary duplication of the
  existing feed catalog and more work to keep metadata coherent.

## Decision: Reuse the existing compatibility formats for list content: JSON, OPML, and plaintext

**Rationale**: The project already supports JSON, OPML, and plaintext for
 podcast subscription import/export, and those formats naturally express a
 collection of podcast feed URLs. Reusing them keeps the user-facing contract
 consistent, avoids new runtime dependencies, and lets create, read, and update
 endpoints share parsing and rendering conventions with the existing sync
 surface.

**Alternatives considered**:
- Support only JSON for lists: simpler, but weaker compatibility than the rest
  of the podcast API surface and less aligned with the supplied format-driven
  endpoints.
- Add HTML or a custom XML format: unnecessary complexity for the current CRUD
  API scope.

## Decision: Generate canonical list names by slugifying titles to lowercase ASCII tokens with hyphen separators and a fallback of `list`

**Rationale**: The spec requires a predictable URL-safe name such as
 `my-python-podcasts` derived from a title. Lowercasing, stripping unsupported
 characters, collapsing separators, and using hyphens matches that expectation
 while remaining easy to explain and test. When normalization would otherwise
 produce an empty result, falling back to `list` preserves deterministic
 behavior without introducing an extra clarification loop.

**Alternatives considered**:
- Reject titles that normalize to an empty slug: stricter, but creates an
  avoidable failure path for a corner case the feature can handle automatically.
- Append random suffixes to avoid collisions: reduces determinism and conflicts
  with the contract that a duplicate generated name should return `409
  Conflict`.

## Decision: Keep duplicate generated names as a user-scoped conflict instead of auto-renaming

**Rationale**: The contract explicitly says the create endpoint returns
 `409 Conflict` when the user already has a podcast list with the generated
 name. Preserving that behavior keeps list URLs stable and forces the client to
 choose a distinct title rather than silently creating `my-list-2` or another
 non-obvious variant.

**Alternatives considered**:
- Auto-append a suffix on collisions: convenient, but contrary to the documented
  conflict behavior and less predictable for callers.
- Enforce global uniqueness across all users: stricter than necessary because
  list URLs are already namespaced by username.

## Decision: Reuse `PodcastFeedModel` as the canonical feed reference and create lightweight placeholder feeds as needed

**Rationale**: Lists are collections of podcasts, and the repository already
 has a canonical feed model used by subscriptions and episodes. Reusing it keeps
 feed URLs deduplicated across features and allows later metadata enrichment to
 benefit list rendering too. Placeholder rows with title defaults are sufficient
 when a list upload references feeds not yet known elsewhere.

**Alternatives considered**:
- Keep feed URLs only inside list items: avoids placeholder rows, but duplicates
  feed identity rules already present in the domain.
- Require feeds to exist before they can appear in lists: too restrictive for a
  compatibility import surface.

## Decision: Order user list summaries by creation time then canonical name, and order list items by explicit position

**Rationale**: Clients and the website need stable outputs across SQLite tests
 and PostgreSQL runtime. Using `created_at` plus canonical name for summaries
 gives predictable chronological ordering without inventing user-custom sort
 preferences. Using an explicit `position` column for list entries preserves the
 submitted order across all supported formats and replacement updates.

**Alternatives considered**:
- Database natural row order: nondeterministic and brittle across engines.
- Alphabetical feed ordering inside a list: predictable, but discards the
  curator's intended sequence.
