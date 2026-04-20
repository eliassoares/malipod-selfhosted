# Research: Directory API

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

## Decisions

### 1) Catalog source of truth

- **Decision**: Directory endpoints query the local database only:
  `podcast_feeds`, `device_subscriptions`, `devices`, `users`, and `episodes`.
- **Rationale**: Spec requires the catalog to be derived exclusively from what
  registered users subscribe to; no external directory is consulted.
- **Alternatives considered**:
  - Fetch/parse RSS feeds at request time: rejected (external IO + performance risk).
  - Use a separate “directory” table: rejected unless required later (would duplicate data).

### 2) Subscriber counting

- **Decision**: `subscribers` is computed as the number of distinct users who
  currently have an active subscription to the feed (via active device
  subscriptions).
- **Rationale**: Matches the spec definition and avoids trusting client-reported
  counts.
- **Alternatives considered**:
  - Use client-provided `subscribers` fields from device updates: rejected (not authoritative).

### 3) `mygpo_link` construction

- **Decision**: Build `mygpo_link` using the server base URL and the local data
  endpoints:
  - Podcast: `<base_url>/api/2/data/podcast.json?url=<feed_url>`
  - Episode: `<base_url>/api/2/data/episode.json?podcast=<feed_url>&url=<media_url>`
- **Rationale**: Satisfies “not hardcoded gpodder.net” and yields a useful local link.
- **Alternatives considered**:
  - Reuse stored `mygpo_link` from `podcast_feeds` / `episodes`: rejected because it may point elsewhere.

### 4) Output formats for `search` and `toplist`

- **Decision**: Support:
  - `.json`: list of podcast objects (see contracts) including at least `url` and `title`
  - `.opml`: OPML document listing feeds (one outline per podcast)
  - `.txt`: one feed URL per line
  Render OPML/TXT using the existing `SubscriptionFormatService` list renderers.
- **Rationale**: Reuses existing rendering logic and keeps behavior consistent with existing list exports.
- **Alternatives considered**:
  - Hand-roll OPML/TXT: rejected (duplicate logic).

### 5) Tags derivation

- **Decision**: Tags are derived from existing stored podcast feed metadata. If
  the repository currently does not persist tags/categories, add a single
  metadata field to `podcast_feeds` (no new table) and ensure it is populated
  during existing feed upsert flows.
- **Rationale**: Meets the spec without adding a separate tag table or performing
  external RSS fetches on directory requests.
- **Alternatives considered**:
  - Empty tags forever: rejected (breaks acceptance scenarios).
  - Add a dedicated tag table: rejected (unnecessary duplication for now).
  - Parse RSS externally: rejected (external dependency + IO).

## Notes

- All endpoints are public and must return useful results with no authentication.
- `count`/`number` parameters are validated (1–100) and out-of-range requests return `400`.
