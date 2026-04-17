# Research: Favorites API

## Decision: Reuse the existing FastAPI app and HTTP Basic ownership helper for the favorites endpoint

**Rationale**: The repository already exposes authenticated compatibility APIs
for subscriptions and episodes using the same FastAPI application and a shared
pattern that authenticates the caller and compares the requested username
against the authenticated account. Reusing that path keeps favorite access
control consistent and avoids inventing a second authentication mechanism for a
single read-only endpoint.

**Alternatives considered**:
- Session-cookie authentication for favorites reads: inconsistent with the
  existing compatibility API surface and less suitable for client sync.
- Endpoint-local custom auth logic: duplicates tested behavior and increases the
  risk of cross-account leakage.

## Decision: Use a dedicated `favorite_episodes` projection table keyed by `(user_id, episode_id)`

**Rationale**: The feature is read-only but still needs a clear source of truth
for which episodes are favorites for one user. A dedicated projection table is
the smallest explicit model that prevents duplicates, keeps favorite ownership
clear, and avoids overloading unrelated episode-action or future settings
structures.

**Alternatives considered**:
- Reuse a future settings-based `is_favorite` flag only: attractive long term,
  but would couple this feature to a separate surface that may not be merged or
  available when this API ships.
- Embed favorite state into `EpisodeActionModel`: conflates playback state with
  a separate user preference concept and makes read semantics less obvious.

## Decision: Source favorite response metadata from existing `EpisodeModel` and `PodcastFeedModel`

**Rationale**: The contract needs episode title, URL, description, website,
release date, public link, and podcast metadata. Those values already belong to
the current episode/feed domain. Reusing those entities keeps the response
consistent with the rest of the sync platform and avoids storing duplicate
metadata snapshots in the favorites table.

**Alternatives considered**:
- Snapshot metadata into the favorites projection: simpler reads, but duplicates
  data and risks drift between favorites and episode records.
- Resolve metadata from remote feeds on demand: adds network complexity and
  violates the repository's current local-domain approach.

## Decision: Order favorites by `favorited_at` descending, then `episode_id` ascending

**Rationale**: Clients need stable results across PostgreSQL runtime and SQLite
tests. Ordering by newest favorite first matches user expectations for a
favorites list, while `episode_id` provides a deterministic tiebreaker when
timestamps are identical.

**Alternatives considered**:
- Natural database row order: nondeterministic and brittle across engines.
- Episode release date order: predictable, but not aligned with when the user
  actually favorited the episode.

## Decision: Return optional metadata fields as null-compatible values instead of dropping favorite items

**Rationale**: Favorite retrieval should remain robust even when some episode or
feed metadata is absent. Returning the item with null-compatible optional fields
preserves the favorite relationship and avoids surprising omissions from the
response.

**Alternatives considered**:
- Exclude incomplete favorites from the response: hides real favorites from the
  user and makes sync behavior less predictable.
- Fail the whole response on incomplete metadata: too strict for a compatibility
  endpoint whose main job is list retrieval.

## Decision: Keep the feature read-only and out of scope for favorite creation or removal

**Rationale**: The user request defines only `GET /api/2/favorites/{username}.json`.
Restricting the scope to retrieval keeps the implementation minimal and focused
while leaving room for other features or website workflows to populate favorite
rows later.

**Alternatives considered**:
- Add POST or DELETE favorites endpoints now: expands scope beyond the supplied
  contract.
- Auto-derive favorites from playback history or popularity: not equivalent to
  user-chosen favorites and introduces recommendation semantics the feature does
  not require.
