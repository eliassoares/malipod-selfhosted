# Data Model: Subscriptions API

## Overview

This feature extends the existing device and podcast-sync persistence model with
format-compatible subscription exports, full-device replacement, and
timestamp-based change retrieval for one device.

## Entity: PodcastFeed

**Purpose**: Represents a canonical podcast subscription target identified by
its feed URL and shared across devices.

**Fields**:
- `id`: internal primary key
- `feed_url`: canonical subscription identifier
- `title`: best-known title for exports that can include metadata
- `description`: optional description text
- `website`: optional website URL
- `logo_url`: optional artwork URL
- `mygpo_link`: optional external catalog link
- `created_at`: first persistence time
- `updated_at`: most recent metadata refresh time

**Validation Rules**:
- `feed_url` must be unique globally
- `feed_url` must represent a sanitized supported URL before it becomes active
- metadata fields may be null when the upload format only supplied feed URLs

**Relationships**:
- Has many `DeviceSubscription` rows
- Has many `Episode` rows from the existing sync domain

## Entity: DeviceSubscription

**Purpose**: Stores whether one device currently subscribes to one podcast
feed.

**Fields**:
- `id`: internal primary key
- `device_pk`: owning device row
- `feed_id`: referenced podcast feed row
- `subscribed_at`: when the feed became active for the device
- `unsubscribed_at`: nullable marker for inactive subscriptions
- `updated_at`: last mutation timestamp for this association

**Validation Rules**:
- `(device_pk, feed_id)` must remain unique
- active subscriptions have `unsubscribed_at = null`
- re-subscribing an existing row clears `unsubscribed_at` and refreshes
  timestamps instead of creating duplicates

**Relationships**:
- Belongs to one `Device`
- Belongs to one `PodcastFeed`
- Produces `SubscriptionChangeEvent` entries when its active state changes

## Entity: SubscriptionChangeEvent

**Purpose**: Records a single add/remove change for one device subscription and
supplies the server-issued integer timestamp used by delta sync.

**Fields**:
- `id`: auto-incrementing integer returned to clients as the sync timestamp
- `device_pk`: owning device row
- `feed_url`: sanitized feed URL associated with the event
- `operation`: `add` or `remove`
- `created_at`: event creation time

**Validation Rules**:
- `operation` must be one of `add` or `remove`
- `feed_url` is stored only for semantically valid sanitized URLs
- events are append-only after creation
- querying with `since = N` returns only rows with `id > N`

**Relationships**:
- Belongs to one `Device`
- Reflects mutations performed through full uploads or delta uploads

## Entity: DeviceSubscriptionExport

**Purpose**: Represents the normalized in-memory shape used to render one feed
into JSON, OPML, or plaintext responses.

**Fields**:
- `url`: feed URL
- `title`: optional title for metadata-rich formats
- `description`: optional description
- `website`: optional website URL
- `logo_url`: optional artwork URL
- `mygpo_link`: optional external catalog URL

**Validation Rules**:
- `url` must be unique within one rendered export set
- metadata fields may be absent without preventing export

**Relationships**:
- Derived from `PodcastFeed` and `DeviceSubscription`
- Used by format renderers only; not persisted directly

## Entity: DeltaUploadRequest

**Purpose**: Represents the normalized client delta payload before persistence.

**Fields**:
- `add`: requested feed URLs to activate
- `remove`: requested feed URLs to deactivate

**Validation Rules**:
- the same sanitized non-empty URL cannot appear in both `add` and `remove`
- duplicate URLs within one list collapse to a single logical operation
- unsupported URLs are rewritten to the empty string and ignored semantically
- the request may be empty, but still yields a fresh server timestamp

**Relationships**:
- Targets one `Device`
- Produces zero or more `SubscriptionChangeEvent` rows plus one response
  `timestamp`

## State Transitions

### Device Subscription Lifecycle

- `absent` -> `active`: full upload or delta upload adds a feed
- `active` -> `inactive`: full upload omission or delta removal sets
  `unsubscribed_at`
- `inactive` -> `active`: later upload reactivates the existing row

### Delta Sync Lifecycle

- `client timestamp = 0` -> `bootstrap delta read`: client receives all changes
  recorded after initial persistence
- `delta upload applied` -> `new timestamp issued`: server returns the highest
  persisted `SubscriptionChangeEvent.id`
- `delta read with prior timestamp` -> `incremental result`: server returns only
  events with `id` greater than the supplied value

## Persistence Notes

- Existing `devices`, `podcast_feeds`, and `device_subscriptions` tables remain
- A new `subscription_change_events` table is introduced for append-only delta
  history
- Full uploads compute a diff between the currently active set and the uploaded
  sanitized set, then persist only the net add/remove changes
- Account-wide reads derive a de-duplicated union from active subscriptions
  across all devices for one user

## Future Extension Notes

This model leaves room for later additions such as feed metadata refresh jobs,
account-level subscription revisions, device deletion cleanup policies, and
episode-state sync integration that references the same feed/device history.
