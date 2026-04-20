# Contract: Home Page (Landing)

## Route

`GET /`

## Rendering Contract

### Shared layout

- MUST use the shared layout (`base.html`) and shared navigation (`partials/topbar.html`).
- MUST be responsive (no horizontal scrolling on mobile).

### Auth-aware CTAs

When unauthenticated:
- MUST show CTA links to `/register` and `/login`.
- MUST NOT show logout CTA.

When authenticated:
- MUST show logout action (POST `/logout`).
- MUST NOT show CTA links to `/register` or `/login`.

### Branding & copy

- MUST contain the brand name “Malipod”.
- MUST NOT contain “gpoddernext” or “Gpodder Next”.
- MUST describe the service as podcast synchronization + gpodder-compatible API endpoints (high level).
