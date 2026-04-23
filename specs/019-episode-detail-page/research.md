# Research: Episode Detail Page

**Feature**: `specs/019-episode-detail-page/spec.md`
**Created**: 2026-04-22

## Decision: Reuse existing episode progress/actions as “progress” source

**Decision**: Display progress using the existing episode action/projection data
already persisted per user and episode (e.g., play positions/started/total when
present).

**Rationale**:
- Avoids introducing new storage for progress, keeping the feature minimal.
- Ensures the page reflects the same truth used by sync endpoints.

**Alternatives considered**:
- New progress table: rejected unless current projection data proves insufficient.

## Decision: Listening history shown as best-effort from existing action events

**Decision**: If event history is available in the existing episode action
events table, show a small list of recent events for the authenticated user.
If it is not available or too expensive to query, show an empty state.

**Rationale**:
- The requirement is “se possível”; implement without expanding scope
significantly.

**Alternatives considered**:
- New dedicated “listening history” store: rejected for v1.

## Decision: Download action depends on presence of a downloadable media URL

**Decision**: Show a download button only when the episode model contains a
downloadable URL field (or can be derived without fetching external resources).
Otherwise hide/disable the action with a clear state.

**Rationale**:
- Avoids pretending we can download when we only have the episode page URL.
- Keeps UX honest and testable.

**Alternatives considered**:
- Fetching/parsing the feed on the fly to find enclosure URLs: rejected for v1
because it adds latency and external dependency to page render.
