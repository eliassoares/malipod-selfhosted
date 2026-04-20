# Contract: `GET /search.{format}`

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

## Request

- **Method**: `GET`
- **Path**: `/search.{format}`
- **Path params**:
  - `format`: `json` | `opml` | `txt`
- **Query params**:
  - `q` (required): search query
- **Authentication**: none (public)

## Response

### `200 OK`

- `format=json`:
  - **Content-Type**: `application/json`
  - **Body**: JSON array of podcast objects (`PodcastDirectoryItem`), possibly empty (`[]`).
- `format=opml`:
  - **Content-Type**: `application/xml`
  - **Body**: OPML document (one outline per feed).
- `format=txt`:
  - **Content-Type**: `text/plain; charset=utf-8`
  - **Body**: one feed URL per line (may be empty).

## Rules

- Search is case-insensitive substring matching on at least podcast title and feed URL.
- Only podcasts present in the local catalog are returned.
