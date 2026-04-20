# Contract: `GET /api/2/data/podcast.json`

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

## Request

- **Method**: `GET`
- **Path**: `/api/2/data/podcast.json`
- **Query params**:
  - `url` (required): feed URL
- **Authentication**: none (public)

## Response

### `200 OK`

- **Content-Type**: `application/json`
- **Body**: podcast metadata object with fields:
  - `url`, `title`, `author`, `description`, `subscribers`, `logo_url`, `website`, `mygpo_link`

### `404 Not Found`

- Feed URL not present in the local catalog.
