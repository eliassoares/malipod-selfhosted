# Data Model: Episodes API

## Overview

This feature extends the existing podcast-sync domain with user-scoped episode
action uploads, append-only action history, filtered retrieval, and aggregated
latest-action reads.

## Entity: PodcastFeed

**Purpose**: Represents the podcast feed to which an episode action belongs.

**Fields**:
- `id`: internal primary key
- `feed_url`: canonical podcast identifier
- `title`: best-known feed title
- `description`: optional feed description
- `website`: optional feed website URL
- `logo_url`: optional artwork URL
- `mygpo_link`: optional external catalog URL
- `created_at`: first persistence time
- `updated_at`: most recent metadata refresh time

**Validation Rules**:
- `feed_url` must be unique globally
- `feed_url` must be sanitized before becoming active in an episode action
- placeholder metadata may be stored when an upload references a feed URL the
  service has not enriched yet

**Relationships**:
- Has many `Episode` rows
- Has many `EpisodeActionEvent` rows indirectly through `Episode`

## Entity: Episode

**Purpose**: Represents one media item identified by its episode URL.

**Fields**:
- `id`: internal primary key
- `feed_id`: owning podcast feed
- `episode_url`: canonical episode media URL
- `title`: best-known episode title
- `description`: optional episode description
- `website`: optional episode website URL
- `mygpo_link`: optional external catalog URL
- `released_at`: best-known release timestamp
- `created_at`: first persistence time
- `updated_at`: most recent metadata refresh time

**Validation Rules**:
- `episode_url` must be unique globally
- `episode_url` must be sanitized before becoming active in an episode action
- placeholder metadata may be stored when an upload references a previously
  unknown episode URL

**Relationships**:
- Belongs to one `PodcastFeed`
- Has many `EpisodeActionEvent` rows
- Has one latest `EpisodeActionState` per user

## Entity: EpisodeActionEvent

**Purpose**: Records one uploaded episode action in append-only form and
supplies the server-issued sync timestamp used by retrieval.

**Fields**:
- `id`: auto-incrementing integer returned to clients as the sync timestamp
- `user_id`: owning account
- `episode_id`: referenced episode
- `podcast_url`: sanitized podcast feed URL captured for compatibility payloads
- `episode_url`: sanitized episode media URL captured for compatibility payloads
- `device_id`: optional device identifier sent by the client
- `action`: one of `download`, `delete`, `play`, `new`, or `flattr`
- `occurred_at`: client-reported action timestamp, or a server default when omitted
- `started`: optional playback start position in seconds
- `position`: optional playback stop position in seconds
- `total`: optional media duration in seconds
- `created_at`: server persistence time for the event

**Validation Rules**:
- `action` must be one of the supported action types
- `podcast_url` and `episode_url` are stored only when both sanitize to
  supported non-empty URLs
- `play` requires `started`, `position`, and `total` together
- non-`play` actions do not use playback progress fields
- retrieval with `since = N` returns only rows with `id > N`
- rows are append-only after creation

**Relationships**:
- Belongs to one `User`
- Belongs to one `Episode`
- May reference one logical device ID string without requiring a device row

## Entity: EpisodeActionState

**Purpose**: Stores the latest known action per user and episode as a projection
used by existing sync logic and aggregated reads.

**Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `device_pk`: optional linked registered device row
- `episode_id`: referenced episode
- `status`: latest action type
- `action`: optional structured payload for playback details or related metadata
- `occurred_at`: latest known event time
- `updated_at`: latest projection refresh time

**Validation Rules**:
- `(user_id, episode_id)` remains unique
- projection values must reflect the latest accepted event for that user and
  episode

**Relationships**:
- Belongs to one `User`
- Belongs to one `Episode`
- May link to one registered `Device`
- Is updated from `EpisodeActionEvent` append operations

## Entity: EpisodeActionQuery

**Purpose**: Represents one retrieval request for episode actions.

**Fields**:
- `since`: optional server-issued timestamp lower bound
- `podcast`: optional podcast URL filter
- `device`: optional device ID filter
- `aggregated`: optional flag requesting only the latest matching action per episode

**Validation Rules**:
- `since` must be greater than or equal to zero when provided
- `podcast` and `device` filters use the same sanitation and validation rules as
  the corresponding upload fields
- aggregation is applied after the requested filters are evaluated

**Relationships**:
- Targets one `User`
- Reads from `EpisodeActionEvent`
- May reuse `EpisodeActionState` semantics for latest-action compatibility

## State Transitions

### Episode Action History Lifecycle

- `absent` -> `event recorded`: valid upload appends a new action event
- `event recorded` -> `latest state updated`: the newest event refreshes the
  latest-state projection for the same user and episode
- `query since N` -> `incremental result`: retrieval returns only events with an
  ID greater than `N`

### Aggregated Retrieval Lifecycle

- `full history result` -> `aggregated result`: matching events collapse to the
  latest event per episode
- `empty match set` -> `empty response`: service still returns an empty `actions`
  list plus a fresh timestamp

## Persistence Notes

- Existing `podcast_feeds`, `episodes`, and `episode_actions` tables remain
- A new `episode_action_events` table is introduced for append-only history
- Uploads create or reuse feed and episode rows, then append history records and
  refresh the latest-state projection
- Device filtering uses the uploaded device ID string and does not require a
  registered device row

## Future Extension Notes

This model leaves room for retention policies, action-log UI screens,
additional action types, account-level replay snapshots, and richer playback
analytics built on top of the same event history.
