# Data Model: Podcast Detail Page

**Feature**: `specs/018-podcast-detail-page/spec.md`
**Created**: 2026-04-22

## Existing Entities (relevant)

### Podcast Feed (`podcast_feeds`)

Represents a podcast and its metadata.

Key fields (existing):
- `id` (primary key)
- `feed_url` (unique)
- `title`, `description`, `website`, `logo_url`

### Episode (`episodes`)

Represents a podcast episode.

Key fields (existing):
- `id` (primary key)
- `feed_id` (FK to `podcast_feeds.id`)
- `title`, `description`, `website`, `logo_url`
- `released_at`

### Subscription (`subscriptions`)

Represents per-device subscription state.

Key fields (existing):
- `device_pk` (FK to devices)
- `feed_id` (FK to `podcast_feeds.id`)
- `subscribed_at`, `unsubscribed_at`

## New Entity: Podcast Favorite

### Favorite Podcast (`favorite_podcasts`)

Stores an account-level preference for marking a podcast as favorite.

Fields:
- `id` (primary key, autoincrement)
- `user_id` (FK to `users.id`, cascade delete)
- `feed_id` (FK to `podcast_feeds.id`, cascade delete)
- `favorited_at` (timezone-aware timestamp)
- `created_at`, `updated_at` (timestamps, consistent with other tables)

Constraints / Indexes:
- Unique constraint on (`user_id`, `feed_id`) to prevent duplicates
- Index on `user_id` to support “favorites-only” filtering
- (Optional) index on `feed_id` if needed for detail-page lookups

Relationships:
- `UserModel.favorite_podcasts` (one-to-many)
- `PodcastFeedModel.favorited_by` (one-to-many)

## Derived Views (query intent)

- **Podcast detail page**: fetch feed by `id`, fetch episodes by `feed_id`,
  determine `(user_id, feed_id)` favorite existence, and determine subscription
  existence for the user (account/device scope depending on existing patterns).
- **Subscriptions page favorites-only filter**: list the user’s subscribed feeds
  and intersect with favorites for that user.
