# Data Model: User Metrics

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/spec.md`
**Date**: 2026-04-23

## Existing Entities Used

### Listening activity

- **Episode Action Events**: per-user, per-episode events with timestamp and optional position/total.
  - Used for: play counts, first/last play timestamps, last-played per podcast, active-day calculations (future), and (optionally) preferred hour / weekday (future).

### Progress snapshot

- **Episode Actions**: per-user, per-episode latest snapshot-like record (best-effort) containing a JSON payload with `position` and `total`.
  - Used for: progress bar and textual progress (“A of B”), completion determination.

### Subscriptions

- **Device Subscriptions**: subscriptions per device; can be aggregated per user to compute “podcasts followed”.
  - Used for: user highlight card “total podcasts followed”.

### Favorites

- **Favorite Episodes**: per-user marker for episodes, includes timestamp.
  - Used for: “favorited at” timestamp on episode page.

## Derived / Computed Views (No New Storage)

### Per-episode metrics (for `/episode/{id}`)

- **Progress**: (position, total) + percentage (if total > 0).
- **Listening activity**: play count; first/last play timestamps.
- **Favorite**: favorited boolean + favorited_at timestamp.

### Per-podcast metrics (for `/podcast/{id}`)

- **Completion rate**: completed episodes / total episodes (when total > 0).
- **In-progress count**: episodes with progress > 0 and not completed.
- **Last played date**: max play event timestamp for episodes in the podcast.

### Cross-podcast metrics (for `/user/{nick}/stats`)

- **Total hours listened**: sum(max position per episode) over all episodes with known progress.
- **Total episodes completed**: count episodes that meet “completed” semantics.
- **Total podcasts followed**: count distinct feeds the user is subscribed to.
- **Rankings**:
  - Top 5 podcasts by time listened (sum of per-episode max position per feed).
  - Top 5 podcasts by completed episodes (count of completed per feed).
- **Temporal insights (future/best-effort)**:
  - hours listened per month (bar chart)
  - preferred hour / weekday
  - active streak

## Validation / Constraints

- All aggregates MUST be scoped to the authenticated user only.
- Cross-account access to user stats MUST return 404 (or equivalent) without leaking existence.
- Empty states MUST be defined and tested for “no events” and “no progress” cases.
