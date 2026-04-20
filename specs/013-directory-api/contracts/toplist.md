# Contract: `GET /toplist/{number}.{format}`

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

## Request

- **Method**: `GET`
- **Path**: `/toplist/{number}.{format}`
- **Path params**:
  - `number`: integer in 1–100
  - `format`: `json` | `opml` | `txt`
- **Authentication**: none (public)

## Response

### `200 OK`

- `format=json`:
  - JSON array of podcast objects (`PodcastDirectoryItem`), possibly empty (`[]`).
- `format=opml`:
  - OPML document.
- `format=txt`:
  - One feed URL per line.

### `400 Bad Request`

- `number` outside 1–100.

## Rules

- Results are ordered by `subscribers` descending.
- Results are limited to `number`.
- Only podcasts present in the local catalog are returned.
