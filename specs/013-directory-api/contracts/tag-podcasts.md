# Contract: `GET /api/2/tag/{tag}/{count}.json`

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

## Request

- **Method**: `GET`
- **Path**: `/api/2/tag/{tag}/{count}.json`
- **Path params**:
  - `tag`: tag identifier
  - `count`: integer in 1–100
- **Authentication**: none (public)

## Response

### `200 OK`

- **Content-Type**: `application/json`
- **Body**: JSON array of podcast objects (`PodcastDirectoryItem`), possibly empty (`[]`).

### `400 Bad Request`

- `count` outside 1–100.

## Rules

- Only podcasts in the local catalog are returned.
- Results are limited to `count`.
