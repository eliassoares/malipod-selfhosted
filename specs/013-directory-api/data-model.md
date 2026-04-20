# Data Model: Directory API

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

This feature is read-only at the API layer and relies on existing persistence
for feeds, subscriptions, and episodes. It introduces response documents (API
contracts) and derived/aggregated fields.

## Runtime Entities (Existing)

- **PodcastFeed**: a feed known by the server (`feed_url`, `title`, `description`, `website`, `logo_url`, …).
- **DeviceSubscription**: active subscriptions per device (`unsubscribed_at is NULL`).
- **Device**: device belongs to a user.
- **User**: subscription ownership and distinct-user counting.
- **Episode**: episode metadata linked to a feed.

## Derived/Aggregated Values

- **Catalog membership**: a feed is “in the catalog” iff it has at least one active subscription (any device) for any user.
- **Subscribers**: count of distinct users with at least one active subscription (any device) to the feed.
- **Tags**: derived from stored feed categories/tags metadata (if present); feeds without categories do not contribute.
- **mygpo_link**: derived from server base URL + local data endpoints.

## Contract Entities (Response Documents)

### PodcastDirectoryItem

- **Represents**: A podcast entry returned by `search` and `toplist`.
- **Fields**:
  - `url` (string): feed URL
  - `title` (string)
  - `description` (string | null)
  - `website` (string | null)
  - `logo_url` (string | null)
  - `subscribers` (integer, >= 0)
  - `mygpo_link` (string)

### TagSummary

- **Represents**: A tag returned by `GET /api/2/tags/{count}.json`.
- **Fields**:
  - `title` (string): human-readable title
  - `tag` (string): tag identifier used in URLs
  - `usage` (integer, >= 0): number of feeds contributing to this tag

### PodcastDataResponse

- **Represents**: `GET /api/2/data/podcast.json?url=<feed_url>`.
- **Fields** (minimum per spec):
  - `url`, `title`, `author` (string | null), `description` (string | null),
    `subscribers` (int), `logo_url` (string | null), `website` (string | null),
    `mygpo_link` (string)

### EpisodeDataResponse

- **Represents**: `GET /api/2/data/episode.json?podcast=<feed>&url=<media>`.
- **Fields** (minimum per spec):
  - `title`, `url`, `podcast_title`, `podcast_url`, `description` (string | null),
    `website` (string | null), `released` (datetime), `mygpo_link` (string | null)
