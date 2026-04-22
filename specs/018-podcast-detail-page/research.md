# Research: Podcast Detail Page

**Feature**: `specs/018-podcast-detail-page/spec.md`
**Created**: 2026-04-22

## Decision: Persist podcast favorites as a dedicated join table

**Decision**: Store a per-user per-podcast favorite flag in a new table with a
uniqueness constraint on `(user_id, feed_id)`.

**Rationale**:
- Favorites need to be queryable for: (1) the podcast detail page state and (2)
  filtering the subscriptions page to only favorites.
- A dedicated table keeps the feature minimal and avoids overloading unrelated
  entities (subscriptions or feeds).

**Alternatives considered**:
- Add a boolean flag on subscriptions: rejected because subscriptions are
  device-scoped and a favorite is an account preference, not a per-device state.
- Store in user settings JSON: rejected because querying/filtering would become
  awkward and less reliable.

## Decision: Expose favorites and subscribe actions as simple authenticated form posts

**Decision**: Use server-rendered pages and standard POST form submissions for
subscribe/favorite actions, matching the existing site patterns.

**Rationale**:
- The existing subscriptions page already uses forms and redirects for
  preferences and adding feeds.
- Keeps the UI functional without requiring a frontend build step or JS-heavy
  flows.

**Alternatives considered**:
- Add a dedicated JS client: rejected to keep scope aligned with existing site.
- Make favorites only available via JSON API first: rejected because the user
  asked for UI actions on the page.

## Decision: Episode ordering based on episode release timestamp

**Decision**: Sort the episode list by the stored release timestamp, with
options for most recent first and oldest first.

**Rationale**:
- The spec requires ordering by date and the episodes table already stores a
  release timestamp.
- Simple to implement and test; avoids requiring new derived fields.

**Alternatives considered**:
- Sort by insertion/update time: rejected because it is not equivalent to
  release date.

## Open Questions (resolved with defaults)

- Should the podcast detail page be accessible even if the user is not
  subscribed? Default: yes for authenticated users; show a clear “subscribe”
  action when not subscribed.
- How to handle podcasts with no imported episodes yet? Default: show an empty
  state with a friendly message; still show metadata.
