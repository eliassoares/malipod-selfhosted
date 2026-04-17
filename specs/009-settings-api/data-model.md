# Data Model: Settings API

## Overview

This feature extends the compatibility API with scoped settings documents. Each
document belongs to one user-owned scope target and stores arbitrary JSON
key-value pairs that can be read or mutated atomically through the API.

## Entity: AccountSettingDocument

**Purpose**: Stores all account-scoped settings for one user.

**Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `settings`: JSON object containing the account-scoped key-value pairs
- `created_at`: first persistence time
- `updated_at`: most recent mutation time

**Validation Rules**:
- `user_id` must be unique so one user has at most one account settings
  document
- `settings` must always be a JSON object, not an array or scalar
- keys are strings
- values may be any valid JSON value

**Relationships**:
- Belongs to one `User`

## Entity: DeviceSettingDocument

**Purpose**: Stores all device-scoped settings for one user-owned device.

**Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `device_id`: referenced device target
- `settings`: JSON object containing device-scoped key-value pairs
- `created_at`: first persistence time
- `updated_at`: most recent mutation time

**Validation Rules**:
- `(user_id, device_id)` must remain unique
- the referenced device must already belong to the same user
- `settings` must always be a JSON object

**Relationships**:
- Belongs to one `User`
- Belongs to one `Device`

## Entity: PodcastSettingDocument

**Purpose**: Stores all podcast-scoped settings for one user and one podcast
feed.

**Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `feed_id`: referenced podcast target
- `settings`: JSON object containing podcast-scoped key-value pairs
- `created_at`: first persistence time
- `updated_at`: most recent mutation time

**Validation Rules**:
- `(user_id, feed_id)` must remain unique
- the referenced feed must exist before the settings document can be created
- `settings` must always be a JSON object

**Relationships**:
- Belongs to one `User`
- Belongs to one `PodcastFeed`

## Entity: EpisodeSettingDocument

**Purpose**: Stores all episode-scoped settings for one user and one episode.

**Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `episode_id`: referenced episode target
- `settings`: JSON object containing episode-scoped key-value pairs
- `created_at`: first persistence time
- `updated_at`: most recent mutation time

**Validation Rules**:
- `(user_id, episode_id)` must remain unique
- the referenced episode must exist before the settings document can be created
- episode scope resolution must confirm that the supplied podcast URL matches
  the episode's feed
- `settings` must always be a JSON object

**Relationships**:
- Belongs to one `User`
- Belongs to one `Episode`
- Indirectly references one `PodcastFeed` through the episode

## Entity: SettingsMutationRequest

**Purpose**: Represents one client request to add, update, and remove keys from
one scoped settings document.

**Fields**:
- `scope`: requested scope name (`account`, `device`, `podcast`, `episode`)
- `podcast`: feed URL query parameter when required by scope
- `device`: device id query parameter when required by scope
- `episode`: episode media URL query parameter when required by scope
- `set`: JSON object of keys to add or replace
- `remove`: ordered list of keys to delete

**Validation Rules**:
- `scope` must be one of the four supported values
- account scope requires no additional query parameters
- device scope requires `device`
- podcast scope requires `podcast`
- episode scope requires both `podcast` and `episode`
- `set` must be a JSON object when present
- `remove` must be an array of strings when present

**Relationships**:
- Resolves to exactly one settings document target
- Produces one resulting JSON settings object after mutation

## Entity: ScopedSettingsResponse

**Purpose**: Represents the JSON object returned by both read and save
operations for one scope target.

**Fields**:
- dynamic string keys for stored settings
- dynamic JSON values for each stored setting

**Validation Rules**:
- response is always a JSON object
- response includes all currently stored keys for the targeted scope
- response excludes removed keys

**Relationships**:
- Derived from one of the four persisted settings document entities

## State Transitions

### Account Scope Lifecycle

- `no document` -> `empty valid scope`: read returns `{}`
- `empty valid scope` -> `persisted`: first write creates `AccountSettingDocument`
- `persisted` -> `persisted updated`: later writes replace or remove keys and
  refresh `updated_at`

### Device Scope Lifecycle

- `missing device` -> `not found`: read or write returns `404`
- `existing device without document` -> `empty valid scope`: read returns `{}`
- `existing device without document` -> `persisted`: first write creates
  `DeviceSettingDocument`
- `persisted` -> `persisted updated`: later writes mutate keys atomically

### Podcast Scope Lifecycle

- `missing feed target` -> `not found`: read or write returns `404`
- `existing feed without document` -> `empty valid scope`: read returns `{}`
- `existing feed without document` -> `persisted`: first write creates
  `PodcastSettingDocument`
- `persisted` -> `persisted updated`: later writes mutate keys atomically

### Episode Scope Lifecycle

- `missing episode target or podcast mismatch` -> `not found`: read or write
  returns `404`
- `existing episode without document` -> `empty valid scope`: read returns `{}`
- `existing episode without document` -> `persisted`: first write creates
  `EpisodeSettingDocument`
- `persisted` -> `persisted updated`: later writes mutate keys atomically

## Persistence Notes

- A new `settings.py` model module will define the four settings tables
- Each table stores one JSON object and timestamps
- Empty reads for valid targets do not require pre-seeded rows
- First successful write lazily creates the corresponding document row
- Writes apply in one transaction per scope request
- Removing unknown keys is a no-op for the stored document

## Future Extension Notes

This model leaves room for future settings metadata such as audit history,
change timestamps per key, website-side feature toggles, or additional scopes
without changing the public request shape introduced by this feature.
