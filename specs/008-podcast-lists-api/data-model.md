# Data Model: Podcast Lists API

## Overview

This feature extends the existing podcast domain with user-owned curated lists,
ordered list membership, deterministic canonical names, and format-compatible
list import/export.

## Entity: PodcastFeed

**Purpose**: Represents the canonical podcast target referenced by list items,
subscriptions, and episodes.

**Fields**:
- `id`: internal primary key
- `feed_url`: canonical podcast identifier
- `title`: best-known podcast title
- `description`: optional feed description
- `website`: optional podcast website URL
- `logo_url`: optional artwork URL
- `mygpo_link`: optional external catalog URL
- `created_at`: first persistence time
- `updated_at`: most recent metadata refresh time

**Validation Rules**:
- `feed_url` must be unique globally
- `feed_url` must pass the project's supported URL sanitation rule before it can
  become active in a list
- placeholder metadata may be stored when list uploads reference a feed URL not
  yet enriched elsewhere in the system

**Relationships**:
- Has many `PodcastListItem` rows
- Has many `DeviceSubscription` rows
- Has many `Episode` rows

## Entity: PodcastList

**Purpose**: Stores one curated podcast collection owned by one user.

**Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `title`: human-readable list title shown in summary responses
- `name`: canonical URL-safe list name generated from the title
- `created_at`: list creation time
- `updated_at`: latest list mutation time

**Validation Rules**:
- `(user_id, name)` must remain unique
- `title` is required and stored separately from the generated canonical name
- `name` must be lowercase, URL-safe, and derived deterministically from the
  submitted title
- when normalization would otherwise yield an empty name, the fallback name is
  `list`

**Relationships**:
- Belongs to one `User`
- Has many ordered `PodcastListItem` rows
- Produces one `PodcastListSummary` view per read request

## Entity: PodcastListItem

**Purpose**: Stores one ordered feed membership inside one podcast list.

**Fields**:
- `id`: internal primary key
- `list_id`: owning list row
- `feed_id`: referenced podcast feed row
- `position`: zero-based or one-based persisted order value used to preserve
  curator-defined sequencing
- `created_at`: first membership persistence time
- `updated_at`: latest membership mutation time

**Validation Rules**:
- `(list_id, feed_id)` must remain unique so the same feed appears at most once
  in one list
- positions must be non-negative and deterministic after create or update
- replacing a list reassigns positions to match the uploaded order

**Relationships**:
- Belongs to one `PodcastList`
- Belongs to one `PodcastFeed`

## Entity: PodcastListSummary

**Purpose**: Represents the compact response item returned by
`GET /api/2/lists/{username}.json`.

**Fields**:
- `title`: human-readable list title
- `name`: canonical list name
- `web`: public website URL for the list

**Validation Rules**:
- `web` must be derivable from the owning username and canonical list name
- one summary item exists per persisted list owned by the requested user
- summary ordering is stable by creation time then canonical name

**Relationships**:
- Derived from `PodcastList`
- Returned in a user-scoped summary collection

## Entity: PodcastListDocument

**Purpose**: Represents the normalized in-memory shape used to parse uploads and
render list reads across JSON, OPML, and plaintext formats.

**Fields**:
- `title`: optional title embedded in the serialized document
- `items`: ordered feed references included in the list
- `format`: requested input or output format

**Validation Rules**:
- `items` preserve the upload order after sanitization and de-duplication
- unsupported or blank feed URLs are ignored semantically during normalization
- the format must be one of the externally supported list formats

**Relationships**:
- Converts between HTTP payloads and persisted `PodcastList` plus
  `PodcastListItem` rows
- Reuses `PodcastFeed` metadata where available

## State Transitions

### Podcast List Lifecycle

- `absent` -> `created`: authenticated create request persists a new
  `PodcastList` and its ordered items
- `created` -> `updated`: authenticated update request replaces the ordered set
  of `PodcastListItem` rows and refreshes `updated_at`
- `created` -> `deleted`: authenticated delete request removes the list and its
  items

### Canonical Name Lifecycle

- `title submitted` -> `name normalized`: create flow slugifies the title
- `normalized name available` -> `persisted`: list is created when no
  same-user conflict exists
- `normalized name collides` -> `conflict`: create request returns `409` and no
  new list is stored

### List Content Lifecycle

- `document uploaded` -> `feed URLs normalized`: parser trims, sanitizes, and
  de-duplicates feed references
- `normalized feeds` -> `ordered items stored`: feeds are resolved or created,
  then written to `PodcastListItem` with stable positions
- `list requested in format X` -> `document rendered`: stored items are
  serialized into the requested supported format

## Persistence Notes

- Existing `podcast_feeds` remains the canonical feed catalog
- A new `podcast_lists` table stores ownership, title, canonical name, and
  timestamps
- A new `podcast_list_items` table stores ordered feed membership per list
- Deleting a list cascades to its items without deleting shared feed rows
- Updating a list replaces its ordered membership while preserving the list row
  and canonical name

## Future Extension Notes

This model leaves room for list descriptions, public/private visibility flags,
list-level metadata, collaborative curation, discovery pages, and richer item
annotations without changing the core ownership and membership structure.
