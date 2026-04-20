# Contract: `GET /api/2/tags/{count}.json`

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

## Request

- **Method**: `GET`
- **Path**: `/api/2/tags/{count}.json`
- **Path params**:
  - `count`: integer in 1–100
- **Authentication**: none (public)

## Response

### `200 OK`

- **Content-Type**: `application/json`
- **Body**: JSON array of tag objects (`TagSummary`), possibly empty (`[]`).

### `400 Bad Request`

- `count` outside 1–100.

## Rules

- Tags are derived from stored feed metadata (categories/tags).
- `usage` is the number of distinct feeds contributing to the tag.
