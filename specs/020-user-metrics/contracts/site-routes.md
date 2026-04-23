# Contracts: Site Routes (User Metrics)

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/spec.md`
**Date**: 2026-04-23

## New Route

### `GET /user/{nickname}/stats`

**Auth**: required (session).
**Authorization**: only the user themselves can view (`nickname` must match current user; otherwise respond as not found).
**Behavior**:
- Renders a server-side HTML page with:
  - highlight cards (hours listened, completed episodes, podcasts followed)
  - rankings Top 5 by time and by completed episodes
  - temporal section placeholders with explicit empty/disabled states when data is insufficient
- Uses the same locale/copy patterns as other site pages and sets locale cookie accordingly.

## Modified Pages (No Route Change)

### `GET /podcast/{id}`

**Header metrics**:
- completion rate (percent of episodes completed)
- episodes in progress
- last played date

**Notes**:
- Must preserve existing header metrics already present (episodes listened, total time listened).
- When metrics are unavailable, show explicit “no data yet” state.

### `GET /episode/{id}`

**Episode metrics**:
- textual progress values (“X% (A of B)”) when possible
- play count, first play date/time, last play date/time derived from play events
- favorite timestamp when favorited

## Navigation

Add a new navigation item “Metrics” between “Subscriptions” and “Logout” that links to:
- `/user/{current_user.nickname}/stats`
