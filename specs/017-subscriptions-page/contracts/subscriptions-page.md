# Contract: Subscriptions Page (SSR)

## Route

`GET /user/subscriptions/{username}`

## Auth & Access Control

- When unauthenticated:
  - MUST redirect to `/login`.
- When authenticated:
  - MUST return 404 if `{username}` does not match the authenticated user nickname.
  - MUST return 404 if the user is deactivated.

## Rendering Contract

### Shared layout

- MUST extend the shared base layout (`app/templates/base.html`).
- MUST render with the existing shared navigation (`partials/topbar.html`).
- MUST be mobile-friendly (no horizontal scrolling; touch targets sized for mobile).

### Subscription list

For each followed podcast, the page MUST show:
- title/name
- image (feed image or placeholder)
- episode count
- last episode timestamp (or an explicit fallback when unknown)

### Search, sort, and view preference

- MUST allow searching by podcast title (case-insensitive).
- MUST allow sorting by:
  - most recent (by last episode date)
  - oldest (by last episode date)
- MUST allow list and grid views and persist the choice for the user.

## i18n

- MUST use the localization `copy[...]` dictionary for all user-visible strings (no hardcoded strings).
