# Data Model: Favorites API

## Overview

This feature extends the compatibility API with authenticated retrieval of one
user's favorite episodes. Favorites are represented as a user-to-episode
projection enriched at read time by existing episode and podcast metadata.

## Entity: FavoriteEpisode

**Purpose**: Represents one episode marked as a favorite for one user.

**Fields**:
- `id`: internal primary key
- `user_id`: owning account
- `episode_id`: referenced episode
- `favorited_at`: time the episode became a favorite for that user
- `created_at`: first persistence time
- `updated_at`: latest persistence refresh time

**Validation Rules**:
- `(user_id, episode_id)` must remain unique so one user cannot favorite the
  same episode more than once in the projection
- the referenced episode must already exist
- the referenced user must already exist
- `favorited_at` is required and used for stable response ordering

**Relationships**:
- Belongs to one `User`
- Belongs to one `Episode`

## Entity: Episode

**Purpose**: Represents the media item returned inside each favorite response
item.

**Fields**:
- `id`: internal primary key
- `feed_id`: owning podcast feed
- `episode_url`: canonical episode media URL
- `title`: best-known episode title
- `description`: optional episode description
- `website`: optional episode website URL
- `mygpo_link`: optional public catalog link
- `released_at`: best-known release timestamp
- `created_at`: first persistence time
- `updated_at`: latest metadata refresh time

**Validation Rules**:
- `episode_url` must be unique globally
- `released_at` may be required at the model level but may still need
  null-compatible response handling if source metadata is incomplete in future
  migrations or imports

**Relationships**:
- Belongs to one `PodcastFeed`
- Has many `FavoriteEpisode` rows

## Entity: PodcastFeed

**Purpose**: Represents the podcast metadata paired with each favorite episode.

**Fields**:
- `id`: internal primary key
- `feed_url`: canonical podcast identifier
- `title`: best-known podcast title
- `description`: optional podcast description
- `website`: optional podcast website URL
- `logo_url`: optional artwork URL
- `mygpo_link`: optional public catalog link
- `created_at`: first persistence time
- `updated_at`: latest metadata refresh time

**Validation Rules**:
- `feed_url` must be unique globally
- the favorites response uses this feed row as the canonical source of podcast
  identity and title

**Relationships**:
- Has many `Episode` rows
- Indirectly supplies metadata to `FavoriteEpisodeResponseItem`

## Entity: FavoriteEpisodeResponseItem

**Purpose**: Represents one serialized favorite episode in
`GET /api/2/favorites/{username}.json`.

**Fields**:
- `title`: episode title
- `url`: episode media URL
- `podcast_title`: podcast title
- `podcast_url`: podcast feed URL
- `description`: optional episode description
- `website`: optional episode website URL
- `released`: optional or null-compatible release timestamp
- `mygpo_link`: optional or null-compatible public episode link

**Validation Rules**:
- one response item exists per favorite projection row
- response items are emitted in stable order by `favorited_at` descending then
  `episode_id` ascending
- required identity fields must always be present
- optional descriptive fields may be null-compatible when source metadata is missing

**Relationships**:
- Derived from `FavoriteEpisode` joined with `Episode` and `PodcastFeed`

## State Transitions

### Favorite Projection Lifecycle

- `absent` -> `favorited`: a separate workflow marks an episode as favorite and
  creates one `FavoriteEpisode` row
- `favorited` -> `favorited refreshed`: metadata or timestamps may be updated
  without changing ownership
- `favorited` -> `unfavorited`: a separate workflow removes the projection row
  and the episode no longer appears in this API

### Favorites Response Lifecycle

- `valid user with no favorites` -> `empty response`: API returns `[]`
- `valid user with favorites` -> `ordered response`: API returns favorite items
  enriched from episode and feed metadata
- `missing user` -> `not found`: API returns the documented not-found response
- `cross-account request` -> `forbidden`: API returns the documented
  ownership-denial response

## Persistence Notes

- A new `favorite_episodes` table stores ownership and ordering timestamps
- Existing `episodes` and `podcast_feeds` remain the canonical metadata source
- Removing a user or episode cascades to favorite rows
- The retrieval path performs relational joins rather than storing copied
  metadata in the favorites projection

## Future Extension Notes

This model leaves room for future favorite creation or removal endpoints,
website-side favorites management, export/import flows, and extra favorite
metadata such as notes or tags without changing the read contract introduced by
this feature.
