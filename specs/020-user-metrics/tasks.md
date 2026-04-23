# Tasks: User Metrics

**Input**: Design documents from `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/`
**Prerequisites**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/plan.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/spec.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/research.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/data-model.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/contracts/site-routes.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/020-user-metrics/quickstart.md`

**Tests**: Add/extend integration coverage for `/user/{nick}/stats`, podcast header metric states, and episode metric states (progress text, plays, first/last, favorited_at), plus run the repository quality gates.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm scope, reuse existing services, and prepare shared helpers.

- [x] T001 Confirm working branch is `020-user-metrics` and feature directory is `specs/020-user-metrics/`
- [x] T002 Review existing metric sources and semantics (completion + time listened) in `app/services/podcast_detail.py` and `app/services/episode_detail.py`
- [x] T003 [P] Add compact duration formatter helper (shared) in `app/core/time_format.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared building blocks used across pages (no UI yet).

**⚠️ CRITICAL**: No user story work should merge without these foundations and tests passing.

- [x] T004 [P] Add User Stats service skeleton and dataclasses in `app/services/user_stats.py`
- [x] T005 [P] Add dependency provider for user stats service in `app/api/deps.py`
- [x] T006 [P] Extend `EpisodeFavoritesService` to expose favorite timestamp (not only boolean) in `app/services/episode_favorites.py`
- [x] T007 [P] Extend `EpisodeDetailService` with play-event aggregate helpers (count/first/last) in `app/services/episode_detail.py`
- [x] T008 [P] Extend `PodcastDetailService` with last-played and completion/in-progress helpers in `app/services/podcast_detail.py`

**Checkpoint**: Services compile and are importable; no UI changes yet.

---

## Phase 3: User Story 1 - Ver métricas do usuário (Priority: P1) 🎯 MVP

**Goal**: Provide `/user/{nickname}/stats` with highlight cards and Top 5 rankings + clear empty states.

**Independent Test**: An authenticated user can GET `/user/{nick}/stats` for themselves, see totals + rankings, and see empty states with no play data; cross-account access returns 404.

### Tests for User Story 1 ⚠️

- [x] T009 [P] [US1] Add integration test for `/user/{nick}/stats` render + access control in `tests/integration/test_user_stats_page.py`
- [x] T010 [P] [US1] Add integration test for empty states (no plays/progress) in `tests/integration/test_user_stats_page.py`
- [x] T011 [P] [US1] Add integration test for Top 5 rankings when listening data exists in `tests/integration/test_user_stats_page.py`

### Implementation for User Story 1

- [x] T012 [P] [US1] Implement user totals + rankings queries in `app/services/user_stats.py`
- [x] T013 [P] [US1] Add site router `GET /user/{nickname}/stats` with locale/copy patterns in `app/api/routes/stats_site.py`
- [x] T014 [US1] Include the new router in `app/main.py`
- [x] T015 [P] [US1] Create user stats template in `app/templates/stats/user_stats.html`
- [x] T016 [P] [US1] Add navigation item “Metrics” (desktop + mobile) in `app/templates/partials/topbar.html`
- [x] T017 [P] [US1] Add localization keys for user stats + nav metrics in `app/core/localization.py`

**Checkpoint**: US1 tests pass and `/user/{nick}/stats` works independently.

---

## Phase 4: User Story 2 - Ver métricas do podcast (Priority: P2)

**Goal**: Add completion rate, in-progress count, and last played date to podcast header without removing existing metrics.

**Independent Test**: With seeded play/progress data, `/podcast/{id}` shows the new metrics; with no play data it shows explicit “no data yet” states.

### Tests for User Story 2 ⚠️

- [x] T018 [P] [US2] Extend integration tests to cover the new podcast header metrics in `tests/integration/test_podcast_detail_page.py`
- [x] T019 [P] [US2] Add integration test for “no play data” empty-state rendering in `tests/integration/test_podcast_detail_page.py`

### Implementation for User Story 2

- [x] T020 [US2] Compute and pass podcast header metrics in `app/api/routes/podcast_site.py` (via helpers in `PodcastDetailService`)
- [x] T021 [P] [US2] Render completion rate / in-progress / last played in the header in `app/templates/podcasts/detail.html`
- [x] T022 [P] [US2] Add localization keys for new podcast header metrics in `app/core/localization.py`

**Checkpoint**: `/podcast/{id}` shows new metrics with correct empty states; tests pass.

---

## Phase 5: User Story 3 - Ver métricas do episódio (Priority: P3)

**Goal**: Add textual progress values, play count + first/last play, and favorited timestamp to `/episode/{id}`.

**Independent Test**: With seeded action events and favorites, `/episode/{id}` shows the new metrics; without data it shows empty states without breaking the page.

### Tests for User Story 3 ⚠️

- [x] T023 [P] [US3] Extend integration tests to cover textual progress values in `tests/integration/test_episode_detail_page.py`
- [x] T024 [P] [US3] Add integration tests for play count + first/last play in `tests/integration/test_episode_detail_page.py`
- [x] T025 [P] [US3] Add integration tests for favorited timestamp visibility in `tests/integration/test_episode_detail_page.py`

### Implementation for User Story 3

- [x] T026 [US3] Query and pass episode play aggregates + favorite timestamp in `app/api/routes/episode_site.py`
- [x] T027 [P] [US3] Render textual progress (“X% (A of B)”) and play aggregates in `app/templates/episodes/detail.html`
- [x] T028 [P] [US3] Render “favorited at” when favorited in `app/templates/episodes/detail.html`
- [x] T029 [P] [US3] Add localization keys for new episode metrics in `app/core/localization.py`

**Checkpoint**: `/episode/{id}` renders all metrics with safe empty states; tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, i18n completeness, and review readiness.

- [x] T030 [P] Ensure mobile responsiveness and basic a11y for stats/cards/labels in `app/templates/stats/user_stats.html`
- [x] T031 Ensure “Metrics” nav item is hidden when logged out (desktop + mobile) in `app/templates/partials/topbar.html`
- [x] T032 Run full quality gates and record evidence in PR summary: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`, `uv run pip-audit`
- [x] T033 Prepare PR summary including scope, verification evidence, metric semantics (completion/time listened), and follow-ups in `PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → required before design-aligned implementation.
- **Foundational (Phase 2)** → shared services that reduce duplication across stories.
- **US1 (Phase 3)** → depends on Phase 2 and delivers the MVP page.
- **US2 (Phase 4)** → can be done after Phase 2 (and independently of US1), but typically after US1.
- **US3 (Phase 5)** → can be done after Phase 2 (and independently of US1/US2), but typically after US1.
- **Polish (Phase 6)** → after desired stories are complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on US2/US3; establishes metrics hub + nav.
- **US2 (P2)**: Independent; reuses PodcastDetailService semantics.
- **US3 (P3)**: Independent; reuses EpisodeDetailService and favorites.

### Parallel Opportunities

- [P] tasks can run in parallel (different files, minimal merge conflicts).
- After Phase 2, US2 and US3 can be implemented in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 + Phase 2
2. Complete Phase 3 (US1)
3. Validate `/user/{nick}/stats` independently (tests + quick browser check)

### Incremental Delivery

1. US1 → US2 → US3
2. Finish with Phase 6 quality gates + PR summary
