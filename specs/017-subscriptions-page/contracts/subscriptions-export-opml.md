# Contract: Export Subscriptions (OPML)

## Route

`GET /user/subscriptions/{username}/export.opml`

## Auth & Access Control

- Same access rules as `GET /user/subscriptions/{username}`.

## Response

- MUST return a valid OPML document containing the authenticated user’s followed feeds.
- MUST include every feed exactly once.
- Media type MUST be `application/xml`.
- The browser MUST download the file (via `Content-Disposition: attachment`).
