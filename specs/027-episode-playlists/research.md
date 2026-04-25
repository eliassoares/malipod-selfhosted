# Research: Episode Playlists

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`
**Date**: 2026-04-25

## Decisions

### Decision: Persistence model for playlists

**Chosen**: Add dedicated tables for episode playlists and playlist memberships.

**Rationale**: Existing `podcast_lists` are feed-based (podcasts). Episode playlists
need different metadata (description, image) and membership uses `episodes`.

**Alternatives considered**:
- Reuse `podcast_lists`: rejected (wrong entity type; would overload semantics and complicate existing list API).

### Decision: “Favorites” as a special playlist

**Chosen**: Treat Favorites as a virtual, read-only playlist in the UI, backed by
existing `favorite_episodes` data. Do not create a row in the playlists table.

**Rationale**: Keeps full compatibility with the existing favorites behavior and
reduces migration risk.

**Alternatives considered**:
- Materialize Favorites into playlists table: rejected (would duplicate source of truth and risk regressions).

### Decision: Playlist image behavior + placeholders

**Chosen**:
- Playlists store an optional `image_url`.
- When absent, the UI displays a placeholder (Malte/Lilith) chosen at random.
- Favorites uses a placeholder as well.

**Rationale**: Matches current placeholder strategy for feeds/episodes while keeping
image optional.

**Alternatives considered**:
- Require images: rejected (adds friction, not required by spec).

### Decision: Upload + export/import interaction

**Chosen**: Export/import preserves playlist metadata and episode memberships; image
is exported/imported as a URL/path string only (no binary transfer). When an imported
image path is not available, the UI falls back to placeholders.

**Rationale**: Keeps snapshot format simple and consistent with existing JSON export;
avoids embedding binary blobs.

**Alternatives considered**:
- Embed base64 image bytes in snapshot: rejected (bloats exports and complicates validation).

### Decision: Playlist metrics computation

**Chosen**:
- Episode count comes from playlist memberships.
- “Listened” and “total” time are derived from existing playback events/progress data,
filtered to episodes in the playlist.

**Rationale**: Reuses the same data source already used for user/podcast metrics and
avoids a new source of truth.
