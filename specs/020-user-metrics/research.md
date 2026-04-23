# Research: User Metrics

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/spec.md`
**Date**: 2026-04-23

## Decisions

### Decision: Episode completion definition

**Chosen**: Reuse the existing “completed episode” semantics already used in podcast episode cards (completion ratio / near-end remaining threshold).

**Rationale**: Keeps user expectations consistent across pages and avoids introducing new rules.

**Alternatives considered**:
- A “completed” flag stored per episode: rejected (new persistence + sync implications).
- Only ratio-based completion: rejected (episodes with unknown duration).

### Decision: Time listened aggregation (user and podcast totals)

**Chosen**: Compute “time listened” as the sum of the maximum known play position per episode, de-duplicated per user+episode.

**Rationale**: Avoids double-counting repeated “play” events and matches the mental model of “how far I got across episodes”.

**Alternatives considered**:
- Sum of all deltas between play events: rejected (no reliable delta modeling today; easily inflates totals).

### Decision: Podcast completion rate / in-progress count

**Chosen**:
- Completion rate = completed episodes / total episodes (for that podcast), expressed as a percentage when total > 0.
- In-progress episodes = episodes with progress > 0 and not completed.

**Rationale**: Simple, explainable, and stable.

### Decision: “Last episode listened” for a podcast

**Chosen**: Use the most recent “play” event timestamp for any episode belonging to the podcast; display the date (and optionally time) in the header.

**Rationale**: Captures actual listening recency even when episode release date differs.

### Decision: Episode metrics (plays, first/last play)

**Chosen**:
- Play count = number of `play` action events for the episode.
- First play = earliest play event timestamp.
- Last play = latest play event timestamp.

**Rationale**: Directly derived and testable; no new persistence.

### Decision: Favorite timestamp on episode page

**Chosen**: When favorited, show the stored favorite timestamp (“favorited on …”).

**Rationale**: Adds context without changing favorite behavior.

### Decision: Streak and temporal insights

**Chosen**: Implement as best-effort and gated by data quality/availability:
- If there is not enough reliable data, show a clear “not enough data yet” state.
- Keep chart/insights visually present but non-misleading.

**Rationale**: Prevents incorrect claims until timestamps are known to be consistent.
