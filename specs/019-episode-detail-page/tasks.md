# Tasks: Episode Detail Page

**Input**: Design documents from `specs/019-episode-detail-page/`
**Prerequisites**: `specs/019-episode-detail-page/plan.md`, `specs/019-episode-detail-page/spec.md`, `specs/019-episode-detail-page/research.md`, `specs/019-episode-detail-page/data-model.md`, `specs/019-episode-detail-page/contracts/site-routes.md`

**Tests**: Add automated coverage for the new episode site routes and the UI states described in the spec. Use existing pytest + TestClient patterns under `tests/`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm baseline, keep scope tight, and prepare scaffolding for the feature.

- [ ] T001 Confirm branch and feature directory alignment in `specs/019-episode-detail-page/spec.md`
- [ ] T002 Confirm template reference assets exist in `google_stitch_templates/malipod_detalhe_do_episodio/code.html`
- [ ] T003 [P] Create template target directory for episode pages in `app/templates/episodes/`
- [ ] T004 Confirm existing episode data model fields for download feasibility in `app/db/models/podcast.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ensure the episode model contains enough information to drive download and the page can query progress/history safely.

**⚠️ CRITICAL**: No user story work should merge without these foundations and tests passing.

- [ ] T005 Add `media_url` (downloadable URL) field to `EpisodeModel` in `app/db/models/podcast.py`
- [ ] T006 Create Alembic migration adding `episodes.media_url` in `alembic/versions/0014_episode_media_url.py`
- [ ] T007 [P] Extend feed import parsing to capture enclosure/media URL for episodes in `app/services/feed_import.py`
- [ ] T008 [P] Upsert `media_url` when importing episodes in `app/services/feed_import.py`
- [ ] T009 [P] Add unit tests for feed parsing of media/enclosure URLs in `tests/unit/test_feed_import_media_url.py`
- [ ] T010 [P] Add small service for toggling favorite episodes (site usage) in `app/services/episode_favorites.py`
- [ ] T011 [P] Add dependency provider for episode favorites service in `app/api/deps.py`
- [ ] T012 [P] Add small service for episode detail queries (episode + progress + history) in `app/services/episode_detail.py`
- [ ] T013 [P] Add dependency provider for episode detail service in `app/api/deps.py`

**Checkpoint**: DB model/migration compiles; feed import tests pass; new services are importable.

---

## Phase 3: User Story 1 - Ver detalhe do episódio (Priority: P1) 🎯 MVP

**Goal**: Render an authenticated episode detail page with metadata and progress.

**Independent Test**: An authenticated user can GET `/episode/{id}` and see metadata + placeholder behavior + progress when present; missing episode returns 404.

### Tests for User Story 1 ⚠️

- [ ] T014 [P] [US1] Add integration test for episode detail render and 404 in `tests/integration/test_episode_detail_page.py`
- [ ] T015 [P] [US1] Add integration test for progress rendering (position/total) in `tests/integration/test_episode_detail_page.py`

### Implementation for User Story 1

- [ ] T016 [P] [US1] Add site router for episode pages in `app/api/routes/episode_site.py`
- [ ] T017 [US1] Include the new router in `app/main.py`
- [ ] T018 [P] [US1] Create `GET /episode/{episode_id}` handler with locale/copy patterns in `app/api/routes/episode_site.py`
- [ ] T019 [P] [US1] Create episode detail template from Stitch reference in `app/templates/episodes/detail.html`
- [ ] T020 [P] [US1] Create episode not-found template in `app/templates/episodes/not_found.html`
- [ ] T021 [P] [US1] Add localization keys for episode detail UI in `app/core/localization.py`
- [ ] T022 [US1] Link episodes list on podcast page to episode detail by wrapping items in `/episode/{id}` in `app/templates/podcasts/detail.html`

**Checkpoint**: US1 tests pass and `/episode/{id}` is usable on its own.

---

## Phase 4: User Story 2 - Baixar e compartilhar episódio (Priority: P2)

**Goal**: Provide download when possible and a share link on the episode page.

**Independent Test**: Download action appears only when `media_url` exists; share link is always available and points to the episode page.

### Tests for User Story 2 ⚠️

- [ ] T023 [P] [US2] Add integration tests for download visibility + download route behavior in `tests/integration/test_episode_detail_page.py`
- [ ] T024 [P] [US2] Add integration test for share link presence in `tests/integration/test_episode_detail_page.py`

### Implementation for User Story 2

- [ ] T025 [US2] Add `GET /episode/{episode_id}/download` handler in `app/api/routes/episode_site.py`
- [ ] T026 [P] [US2] Add download UI state (hidden/disabled) based on `media_url` in `app/templates/episodes/detail.html`
- [ ] T027 [P] [US2] Add share UI that exposes the episode page URL in `app/templates/episodes/detail.html`
- [ ] T028 [P] [US2] Add localization keys for download/share UI in `app/core/localization.py`

**Checkpoint**: Download/share behavior covered by tests and matches visibility rules.

---

## Phase 5: User Story 3 - Favoritar e ver histórico de ouvidas (Priority: P3)

**Goal**: Toggle favorite episodes and show listening history (best-effort).

**Independent Test**: Favoriting persists across reload; history section shows events when present and a clear empty state when not.

### Tests for User Story 3 ⚠️

- [ ] T029 [P] [US3] Add integration test for favorite toggle persistence in `tests/integration/test_episode_detail_page.py`
- [ ] T030 [P] [US3] Add integration test for listening history section (events and empty state) in `tests/integration/test_episode_detail_page.py`

### Implementation for User Story 3

- [ ] T031 [US3] Add `POST /episode/{episode_id}/favorite` handler in `app/api/routes/episode_site.py`
- [ ] T032 [P] [US3] Add favorite UI controls to the episode template in `app/templates/episodes/detail.html`
- [ ] T033 [P] [US3] Add localization keys for favorite/history UI in `app/core/localization.py`
- [ ] T034 [US3] Implement history query (recent action events) in `app/services/episode_detail.py`
- [ ] T035 [P] [US3] Render history section with empty state in `app/templates/episodes/detail.html`

**Checkpoint**: Favorite + history works end-to-end and is tested.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, correctness, and review readiness.

- [ ] T036 [P] Ensure mobile responsiveness and basic a11y (labels/sr-only) in `app/templates/episodes/detail.html`
- [ ] T037 Run full quality gates and record evidence in PR summary: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`
- [ ] T038 Prepare PR summary including scope, verification evidence, and follow-ups in `PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → required before making structural edits.
- **Foundational (Phase 2)** → blocks reliable download behavior and site actions wiring.
- **US1 (Phase 3)** → depends on Phase 2 and delivers the page shell.
- **US2 (Phase 4)** → depends on `media_url` foundation and the page context from US1.
- **US3 (Phase 5)** → depends on existing favorites/actions entities and the page context from US1.
- **Polish (Phase 6)** → after user stories are complete.

### Parallel Opportunities

- [P] tasks touch separate files and can be split across team members.
- Tests per story can be written in parallel with scaffolding, but should fail before the implementation that satisfies them.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 + Phase 2
2. Complete Phase 3 (US1)
3. Validate `/episode/{id}` render and 404 behavior

### Incremental Delivery

1. US1 → US2 (download/share) → US3 (favorite/history)
2. Finish with Phase 6 polish and quality gates
