# Tasks: Episode Playlists

**Input**: Design documents from `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/`
**Prerequisites**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/plan.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/research.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/data-model.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/contracts/`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/quickstart.md`

**Tests**: Add integration coverage for playlist CRUD, owner-only access, favorites-as-playlist rendering, add/remove episode membership, episode-detail “add to playlist” popup flow, and snapshot export/import round-trip for playlists.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing primitives (episodes, favorites, user data tools, placeholders) and identify the best integration points.

- [x] T001 Confirm working branch is `027-episode-playlists` and feature directory is `specs/027-episode-playlists/`
- [x] T002 Review existing favorites, episode detail page, and placeholder utilities (`app/db/models/podcast.py`, `app/services/user_stats.py`, `app/core/placeholders.py`, `app/templates/episode/detail.html`)
- [x] T003 Review user data tools snapshot export/import flow and existing snapshot schemas (`app/services/user_data_tools.py`, `app/schemas/user_data_tools.py`, `app/api/routes/profile_site.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add playlist persistence and baseline services to support all user stories.

**⚠️ CRITICAL**: No UI work should ship without owner-only enforcement and input validation.

- [x] T004 Add new DB models for episode playlists + memberships in `app/db/models/podcast.py`
- [x] T005 Add Alembic migrations for episode playlists tables in `alembic/versions/0016_episode_playlists.py`
- [x] T006 Implement playlist placeholder selection rules (playlist image_url fallback, favorites placeholder) in `app/core/placeholders.py` or a new helper under `app/core/`
- [x] T007 Implement `EpisodePlaylistsService` for CRUD + membership operations in `app/services/episode_playlists.py`
- [x] T008 [P] Add schemas for playlist pages (context payloads) under `app/schemas/episode_playlists.py`

**Checkpoint**: Playlists can be persisted, validated, and queried per user; no cross-account reads.

---

## Phase 3: User Story 1 - Gerenciar playlists (Priority: P1) 🎯 MVP

**Goal**: User can manage playlists (list/create/edit/delete) and see Favorites listed as read-only playlist.

**Independent Test**: A logged-in user can create/edit/delete a playlist from the management page; Favorites appears but cannot be edited or deleted; owner-only is enforced.

### Tests for User Story 1 ⚠️

- [x] T009 [P] [US1] Add integration tests for playlist management page render + Favorites listed in `tests/integration/test_episode_playlists_page.py`
- [x] T010 [P] [US1] Add integration tests for playlist create/update validation (1024 desc, 1MB image) in `tests/integration/test_episode_playlists_page.py`
- [x] T011 [P] [US1] Add integration tests for delete confirmation flow and owner-only enforcement in `tests/integration/test_episode_playlists_page.py`

### Implementation for User Story 1

- [x] T012 [US1] Add site routes for manage/create/update/delete in `app/api/routes/episode_playlists_site.py`
- [x] T013 [US1] Add templates for manage page + modals in `app/templates/playlists/manage.html`
- [x] T014 [US1] Add navigation entry “Playlists” (localized) in `app/core/localization.py` + base template nav (`app/templates/base.html`)

**Checkpoint**: US1 tests pass; management page works and is mobile friendly + localized.

---

## Phase 4: User Story 2 - Visualizar detalhes e métricas da playlist (Priority: P2)

**Goal**: User can view a playlist detail page with metrics + list of episodes; add/remove episodes via search.

**Independent Test**: Create a playlist, add 1+ episodes, open playlist detail page and see expected metrics and episode list.

### Tests for User Story 2 ⚠️

- [x] T015 [P] [US2] Add integration test for playlist detail page rendering + placeholder behavior in `tests/integration/test_episode_playlist_detail_page.py`
- [x] T016 [P] [US2] Add integration test for adding/removing episodes via playlist detail page in `tests/integration/test_episode_playlist_detail_page.py`

### Implementation for User Story 2

- [x] T017 [US2] Implement detail route + search/add/remove handlers in `app/api/routes/episode_playlists_site.py`
- [x] T018 [US2] Add playlist detail template with metrics + episodes list + search UI in `app/templates/playlists/detail.html`
- [x] T019 [US2] Implement playlist metrics derivation in `app/services/episode_playlists.py` (episode count, listened seconds, total seconds, created_at)

**Checkpoint**: US2 tests pass; detail page is consistent with site styling and shows metrics.

---

## Phase 5: User Story 3 - Adicionar episódio a playlists (Priority: P3)

**Goal**: Episode detail page lets user add the episode to multiple playlists via popup.

**Independent Test**: From an episode detail page, select multiple playlists and confirm the episode appears in each playlist.

### Tests for User Story 3 ⚠️

- [x] T020 [P] [US3] Add integration test for episode detail “add to playlist” popup flow in `tests/integration/test_episode_detail_add_to_playlist.py`

### Implementation for User Story 3

- [x] T021 [US3] Add episode detail page button + popup UI in `app/templates/episodes/detail.html`
- [x] T022 [US3] Add route to handle multi-playlist membership submission in `app/api/routes/episode_playlists_site.py`
- [x] T023 [US3] Ensure service prevents duplicates and enforces owner-only playlist membership writes in `app/services/episode_playlists.py`

**Checkpoint**: US3 tests pass and user can add to multiple playlists in one action.

---

## Phase 6: Export/Import Integration (Cross-cutting)

**Purpose**: Include playlists in user data export/import.

- [ ] T024 Add snapshot schemas for playlists in `app/schemas/user_data_tools.py`
- [ ] T025 Implement export of playlists + playlist items in `app/services/user_data_tools.py`
- [ ] T026 Implement import of playlists + playlist items with id mapping in `app/services/user_data_tools.py`
- [ ] T027 [P] Add tests for snapshot round-trip including playlists in `tests/unit/test_user_data_tools.py`

**Checkpoint**: Export/import preserves playlists and memberships; Favorites remains unchanged.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates and PR readiness.

- [ ] T028 Run full quality gates: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`, `uv run pip-audit`
- [ ] T029 Validate manual steps in `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/quickstart.md`
- [ ] T030 Prepare PR summary (scope, screenshots optional, verification evidence, follow-ups) in `PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → required to locate current integration points.
- **Foundational (Phase 2)** → blocks UI and export/import work.
- **US1 (Phase 3)** → depends on Phase 2; delivers MVP (manage playlists + Favorites listed).
- **US2 (Phase 4)** → depends on Phase 2; adds details + metrics + membership management.
- **US3 (Phase 5)** → depends on Phase 2; integrates episode detail add flow.
- **Export/Import (Phase 6)** → depends on Phase 2; can be done after US1 or later.
- **Polish (Phase 7)** → after desired stories complete.

### User Story Dependencies

- **US1 (P1)**: Foundation for everything else.
- **US2 (P2)**: Adds value without changing US1 behavior.
- **US3 (P3)**: Adds convenience; depends on playlist existence.

### Parallel Opportunities

- [P] test tasks in different files can proceed once Phase 2 is complete.
- [P] snapshot schema work can be done in parallel with site pages, but only after models exist.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. Validate CRUD + Favorites listed + owner-only

### Incremental Delivery

1. US1 → US2 → US3
2. Add export/import (Phase 6)
3. Finish with Phase 7 quality gates + PR summary
