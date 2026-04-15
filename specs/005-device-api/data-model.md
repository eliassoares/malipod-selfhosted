# Data Model: Device API

## Overview

This feature introduces the first persistent device and sync-domain entities for
Malipod. The model is intentionally small but sufficient to support
client-generated device identities, per-device subscription visibility, and
incremental episode update retrieval for authenticated users.

## Entity: Device

**Purpose**: Represents one client application instance registered under a user
account and used to scope sync behavior.

**Fields**:
- `id`: internal numeric identifier
- `user_id`: owning account
- `device_id`: client-generated external identifier
- `caption`: human-readable display label
- `device_type`: supported device category
- `created_at`: time the device record was created
- `updated_at`: time the device metadata was last changed

**Validation Rules**:
- `device_id` must match `[\\w.-]+`
- `device_id` must be unique within a single `user_id`
- `device_type` must be one of `desktop`, `laptop`, `mobile`, `server`, or
  `other`
- `caption` may be empty but must be storable as a normal string

**Relationships**:
- Belongs to one `User`
- Has many `DeviceSubscription` records
- Has many device-scoped update lookups

## Entity: PodcastFeed

**Purpose**: Represents one canonical podcast subscription target that can be
attached to one or more devices.

**Fields**:
- `id`: internal numeric identifier
- `feed_url`: canonical subscription URL
- `title`: feed title shown to clients
- `description`: optional feed description
- `website`: optional feed website URL
- `logo_url`: optional artwork URL
- `mygpo_link`: optional public service link
- `created_at`: time the feed entered local persistence
- `updated_at`: time feed metadata last changed

**Validation Rules**:
- `feed_url` must be unique
- optional URLs must be valid URL strings when present
- metadata fields must be safe to return to API clients without additional
  formatting rules

**Relationships**:
- Linked to many `DeviceSubscription` records
- Owns many `Episode` records

## Entity: DeviceSubscription

**Purpose**: Represents a feed currently or previously associated with a
specific device.

**Fields**:
- `device_id`: owning device
- `feed_id`: subscribed feed
- `subscribed_at`: time the feed became active for the device
- `unsubscribed_at`: nullable time the feed was removed for the device
- `updated_at`: time the subscription relationship last changed

**Validation Rules**:
- only one active subscription may exist for a given device/feed pair
- `unsubscribed_at` must be later than or equal to `subscribed_at` when present
- active subscriptions are counted in the device list response

**Relationships**:
- Belongs to one `Device`
- Belongs to one `PodcastFeed`

## Entity: Episode

**Purpose**: Represents one canonical podcast episode that may appear in device
update responses.

**Fields**:
- `id`: internal numeric identifier
- `feed_id`: parent podcast feed
- `episode_url`: canonical episode media URL
- `title`: episode title
- `description`: optional episode summary
- `website`: optional episode landing page
- `mygpo_link`: optional public service link
- `released_at`: episode release timestamp
- `created_at`: time the episode was recorded locally
- `updated_at`: time episode metadata last changed

**Validation Rules**:
- `episode_url` must be unique
- `released_at` must be timezone-aware
- the parent feed must exist before an episode can be stored

**Relationships**:
- Belongs to one `PodcastFeed`
- Has many `EpisodeAction` records

## Entity: EpisodeAction

**Purpose**: Represents the latest sync-relevant state reported for one episode
for a user and, when relevant, its originating device.

**Fields**:
- `id`: internal numeric identifier
- `user_id`: owning account
- `device_id`: nullable originating device
- `episode_id`: related episode
- `status`: one of `new`, `play`, `download`, or `delete`
- `action`: nullable structured latest action payload returned when requested
- `occurred_at`: time the action was reported
- `updated_at`: time this latest-state record last changed

**Validation Rules**:
- one latest-state record must exist per user/episode combination
- `status` must match the externally documented allowed values
- `action` is required in stored form only when the latest state is not `new`
- `occurred_at` must be timezone-aware and is the primary timestamp for `since`
  filtering of episode updates

**Relationships**:
- Belongs to one `User`
- May reference one `Device`
- Belongs to one `Episode`

## State Transitions

### Device Lifecycle

- `absent` → `registered`: authenticated create-or-update request creates the
  device row
- `registered` → `registered`: later requests partially update caption or type
- `registered` → `registered with subscriptions`: one or more active
  `DeviceSubscription` records are attached

### Device Subscription Lifecycle

- `inactive` → `active`: feed is associated with the device
- `active` → `active`: feed metadata changes without removing the association
- `active` → `removed`: `unsubscribed_at` is recorded and the feed appears in
  the `remove` collection for sync windows that include the change

### Episode Update Lifecycle

- `unseen` → `new`: episode exists for the user/device sync context with no
  non-default action yet
- `new` → `play`: playback activity updates the latest episode state
- `play` → `download`: download activity becomes the latest episode state
- `play|download` → `delete`: deletion becomes the latest episode state

## Future Extension Notes

This model intentionally leaves room for later feed discovery, full subscription
management endpoints, richer episode-action history, and broader gpodder sync
contracts without forcing a rewrite of the device ownership boundary introduced
here.
