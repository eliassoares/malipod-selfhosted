# Tasks: Podcast Detail Page

**Input**: Design documents from `specs/018-podcast-detail-page/`
**Prerequisites**: `specs/018-podcast-detail-page/plan.md`, `specs/018-podcast-detail-page/spec.md`, `specs/018-podcast-detail-page/research.md`, `specs/018-podcast-detail-page/data-model.md`, `specs/018-podcast-detail-page/contracts/site-routes.md`

**Tests**: Add automated coverage for new site routes and favorites filtering. Use existing pytest + TestClient patterns under `tests/`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm baseline, keep scope tight, and prepare scaffolding for the feature.

- [x] T001 Confirm branch and feature directory alignment in `specs/018-podcast-detail-page/spec.md`
- [x] T002 Confirm route inclusion points and existing site patterns in `app/main.py`
- [x] T003 [P] Capture the new Google Stitch reference into repo (already present) and confirm template assets in `google_stitch_templates/malipod_detalhe_do_podcast/code.html`
- [x] T004 [P] Create template target directory for new page in `app/templates/podcasts/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DB + service primitives that must exist before UI stories can be completed.

**⚠️ CRITICAL**: No user story work should merge without these foundations and tests passing.

- [x] T005 Create DB model for favorite podcasts in `app/db/models/podcast.py`
- [x] T006 [P] Add user relationship for favorite podcasts in `app/db/models/user.py`
- [x] T007 [P] Add feed relationship for being favorited in `app/db/models/podcast.py`
- [x] T008 Create Alembic migration for `favorite_podcasts` table in `alembic/versions/0013_favorite_podcasts.py`
- [x] T009 [P] Add minimal service for podcast favorites CRUD/toggle in `app/services/podcast_favorites.py`
- [x] T010 [P] Add dependency provider for podcast favorites service in `app/api/deps.py`
- [x] T011 [P] Add unit tests for podcast favorites service behavior in `tests/unit/test_podcast_favorites_service.py`

**Checkpoint**: DB migration + model + service compile and unit tests pass.

---

## Phase 3: User Story 1 - Ver detalhe do podcast e seus episódios (Priority: P1) 🎯 MVP

**Goal**: Render a podcast detail page with podcast metadata and full episode list.

**Independent Test**: An authenticated user can GET `/podcast/{id}` and see podcast metadata + episode list; missing podcast returns 404; missing images fall back to placeholders.

### Tests for User Story 1 ⚠️

- [x] T012 [P] [US1] Add integration test for 404 and basic render in `tests/integration/test_podcast_detail_page.py`
- [x] T013 [P] [US1] Add integration test for placeholder rendering in `tests/integration/test_podcast_detail_page.py`

### Implementation for User Story 1

- [x] T014 [P] [US1] Add a podcast detail query/service (feed + episode list) in `app/services/podcast_detail.py`
- [x] T015 [P] [US1] Add site router for podcast pages in `app/api/routes/podcast_site.py`
- [x] T016 [US1] Include the new router in `app/main.py`
- [x] T017 [P] [US1] Create the podcast detail template based on Stitch reference in `app/templates/podcasts/detail.html`
- [x] T018 [P] [US1] Add localization keys for the podcast detail page in `app/core/localization.py`
- [x] T019 [US1] Wire GET `/podcast/{id}` to render template with locale/copy patterns in `app/api/routes/podcast_site.py`
- [x] T020 [US1] Update subscriptions cards to link to `/podcast/{id}` by adding `feed_id` to the view model in `app/schemas/subscriptions_page.py`
- [x] T021 [US1] Populate `feed_id` in `app/services/subscriptions_page.py`
- [x] T022 [US1] Make subscriptions UI items clickable and keep mobile layout intact in `app/templates/subscriptions/index.html`

**Checkpoint**: US1 tests pass and `/podcast/{id}` is usable on its own.

---

## Phase 4: User Story 2 - Ordenar episódios por data (Priority: P2)

**Goal**: Allow sorting the episode list by most recent / oldest.

**Independent Test**: With two episodes in different dates, `sort=recent` and `sort=oldest` produce opposite ordering.

### Tests for User Story 2 ⚠️

- [x] T023 [P] [US2] Add integration test asserting `recent` vs `oldest` ordering in `tests/integration/test_podcast_detail_page.py`

### Implementation for User Story 2

- [x] T024 [US2] Add `sort` query parameter handling to GET `/podcast/{id}` in `app/api/routes/podcast_site.py`
- [x] T025 [US2] Implement order-by logic in the query layer in `app/services/podcast_detail.py`
- [x] T026 [P] [US2] Add UI control for episode ordering (mobile-friendly) in `app/templates/podcasts/detail.html`
- [x] T027 [P] [US2] Add localization keys for episode ordering UI in `app/core/localization.py`

**Checkpoint**: Sorting works and is covered by tests.

---

## Phase 5: User Story 3 - Inscrever e favoritar podcast (Priority: P3)

**Goal**: Provide subscribe action when not subscribed, and favorite/unfavorite toggle.

**Independent Test**: A user not subscribed sees “subscribe”, can subscribe, and can favorite/unfavorite with persistence across reload.

### Tests for User Story 3 ⚠️

- [x] T028 [P] [US3] Add integration test for subscribe visibility + action redirect in `tests/integration/test_podcast_detail_page.py`
- [x] T029 [P] [US3] Add integration test for favorite toggle persistence in `tests/integration/test_podcast_detail_page.py`

### Implementation for User Story 3

- [x] T030 [US3] Add helper to detect whether the user is subscribed to a feed in `app/services/subscriptions_page.py`
- [x] T031 [US3] Expose “is_subscribed” on podcast detail context in `app/services/podcast_detail.py`
- [x] T032 [US3] Implement POST `/podcast/{id}/subscribe` (idempotent) in `app/api/routes/podcast_site.py`
- [x] T033 [US3] Implement POST `/podcast/{id}/favorite` (toggle) in `app/api/routes/podcast_site.py`
- [x] T034 [P] [US3] Add subscribe + favorite UI controls in `app/templates/podcasts/detail.html`
- [x] T035 [P] [US3] Add localization keys for subscribe/favorite actions in `app/core/localization.py`

**Checkpoint**: Subscribe and favorite flows work end-to-end.

---

## Phase 6: User Story 4 - Filtrar subscrições por favoritos (Priority: P4)

**Goal**: Add a favorites-only filter to the subscriptions page.

**Independent Test**: With 2 subscriptions and only 1 favorited, enabling the filter shows only the favorited feed and provides an empty state when none exist.

### Tests for User Story 4 ⚠️

- [x] T036 [P] [US4] Add integration test for favorites-only filtering in `tests/integration/test_subscriptions_page_favorites.py`

### Implementation for User Story 4

- [x] T037 [US4] Extend `SubscriptionsQuery` to include favorites-only flag in `app/services/subscriptions_page.py`
- [x] T038 [US4] Join against favorites to filter in `app/services/subscriptions_page.py`
- [x] T039 [US4] Thread the `favorites` query param through the route in `app/api/routes/subscriptions_site.py`
- [x] T040 [P] [US4] Add filter UI toggle (favorites only) in `app/templates/subscriptions/index.html`
- [x] T041 [P] [US4] Add localization keys for favorites-only filter + empty state in `app/core/localization.py`

**Checkpoint**: Filter is usable, localized, and tested.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, correctness, and review readiness.

- [x] T042 [P] Ensure feed import populates author/categories when present (best-effort) in `app/services/feed_import.py`
- [x] T043 [P] Add unit tests for feed parsing of author/categories (best-effort) in `tests/unit/test_feed_import_metadata.py`
- [x] T044 Verify mobile responsiveness and a11y basics (labels, sr-only) in `app/templates/podcasts/detail.html`
- [x] T045 Run full quality gates and record evidence in PR summary: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`
- [x] T046 Prepare PR summary including scope, verification evidence, and follow-ups in `PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → required before making structural edits.
- **Foundational (Phase 2)** → blocks podcast favoriting and favorites-only filtering.
- **US1 (Phase 3)** → depends on Phase 2 and enables the detail page shell.
- **US2 (Phase 4)** → depends on US1 page context.
- **US3 (Phase 5)** → depends on favorites foundation (Phase 2) and US1 page context.
- **US4 (Phase 6)** → depends on favorites foundation (Phase 2) and existing subscriptions page route/template.
- **Polish (Phase 7)** → after user stories are complete.

### Parallel Opportunities

- [P] tasks are designed to touch separate files and can be split across team members.
- Tests for a given user story can be written in parallel with model/service scaffolding (but should fail before implementation).

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 + Phase 2
2. Complete Phase 3 (US1)
3. Validate `/podcast/{id}` render and 404 behavior

### Incremental Delivery

1. US1 → US2 (sorting) → US3 (subscribe/favorite) → US4 (favorites filter)
2. Finish with Phase 7 polish and quality gates
