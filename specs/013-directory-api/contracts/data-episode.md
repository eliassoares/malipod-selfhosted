# Contract: `GET /api/2/data/episode.json`

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

## Request

- **Method**: `GET`
- **Path**: `/api/2/data/episode.json`
- **Query params**:
  - `podcast` (required): feed URL
  - `url` (required): media URL
- **Authentication**: none (public)

## Response

### `200 OK`

- **Content-Type**: `application/json`
- **Body**: episode metadata object with fields:
  - `title`, `url`, `podcast_title`, `podcast_url`, `description`, `website`, `released`, `mygpo_link`

### `404 Not Found`

- Feed URL not present in the local catalog, or the episode is not found.
