# Contract: `GET /clientconfig.json`

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/spec.md`

## Purpose

Allow gpodder-compatible clients to auto-discover the server base URL and refresh
interval without any authentication or manual configuration.

## Request

- **Method**: `GET`
- **Path**: `/clientconfig.json`
- **Authentication**: none (public)
- **Headers**: none required

## Response

### `200 OK`

- **Content-Type**: `application/json`
- **Body**:

```json
{
  "mygpo": { "baseurl": "https://example.com/" },
  "mygpo-feedservice": { "baseurl": "https://example.com/" },
  "update_timeout": 86400
}
```

## Rules

- `mygpo.baseurl` must reflect the server’s configured base URL.
- `mygpo.baseurl` must be normalized to include a trailing slash.
- Response must be JSON even if the request has no `Accept` header.
- `update_timeout` must be a positive integer (seconds).

## Non-goals

- No user identification, no personalization, no database writes.
