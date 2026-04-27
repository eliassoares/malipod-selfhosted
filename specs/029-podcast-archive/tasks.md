# Tasks: Podcast Archive

**Input**: Design documents from `/specs/029-podcast-archive/`
**Prerequisites**: `specs/029-podcast-archive/plan.md` (required), `specs/029-podcast-archive/spec.md` (required), `specs/029-podcast-archive/research.md`, `specs/029-podcast-archive/data-model.md`, `specs/029-podcast-archive/contracts/`

**Tests**: Required by spec (NFR-001): unit + contract + integration coverage for enable/disable, idempotent queueing, and safe cleanup.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Task descriptions include exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm repo state and prepare feature scaffolding

- [X] T001 Confirm working branch is `029-podcast-archive` and feature docs exist in `specs/029-podcast-archive/`
- [X] T002 Inspect current alembic head(s) and choose next revision number for `alembic/versions/` (avoid collisions)
- [X] T003 Inspect existing `app/api/routes/` and `app/templates/podcasts/detail.html` patterns for site-form POST/DELETE actions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add config entries `ARCHIVE_DIR`, `ARCHIVE_WORKERS`, `ARCHIVE_SYNC_INTERVAL_MINUTES` in `app/core/config.py`
- [X] T005 Add DB fields to models (`PodcastFeed.archive`, `Episode.archive_status/archive_path/archive_error`) in `app/db/models/podcast.py`
- [X] T006 Create alembic migration adding the new columns in `alembic/versions/00XX_podcast_archive.py`
- [X] T007 [P] Implement archive path helpers (slugify + safe join + confinement checks) in `app/services/archive_paths.py`
- [X] T008 Implement queue state transitions + idempotent enqueue/cancel in `app/services/archive_queue.py`
- [X] T009 Implement async download worker(s) with streaming write + status updates in `app/services/archive_worker.py`
- [X] T010 Implement periodic sync loop (asyncio task + sleep) in `app/services/archive_scheduler.py`
- [X] T011 Implement safe cleanup (delete only within `ARCHIVE_DIR`, based on DB-known relative paths) in `app/services/archive_cleanup.py`
- [X] T012 Wire archive queue/workers/scheduler into FastAPI lifespan startup/shutdown in `app/main.py` (or the existing app factory/module used by Uvicorn)
- [X] T013 [P] Add localization keys for archive UI labels/statuses in `app/core/localization.py`

**Checkpoint**: Foundation ready — routes/UI/tests can now be implemented per user story

---

## Phase 3: User Story 1 - Ativar arquivamento de um podcast (Priority: P1) 🎯 MVP

**Goal**: User can enable archive on a podcast; episodes are queued/downloaded; UI shows per-episode status and links to completed files.

**Independent Test**: Enable archive for a podcast and see episodes move `none → queued → downloading → done` with files created under `ARCHIVE_DIR`.

### Tests for User Story 1 ⚠️

- [X] T014 [P] [US1] Unit tests for slugify + confinement helpers in `tests/unit/test_archive_paths.py`
- [X] T015 [P] [US1] Unit tests for idempotent enqueue behavior in `tests/unit/test_archive_queue.py`
- [X] T016 [P] [US1] Contract tests for `POST /podcast/{id}/archive` in `tests/contract/test_podcast_archive_site.py`
- [X] T017 [P] [US1] Integration test: enabling archive queues episodes and creates files (mock media HTTP) in `tests/integration/test_podcast_archive_download.py`

### Implementation for User Story 1

- [X] T018 [US1] Add `POST /podcast/{id}/archive` route (auth required) in `app/api/routes/podcast_archive_site.py`
- [X] T019 [US1] Update router inclusion for `app/api/routes/podcast_archive_site.py` in `app/api/routes/__init__.py` (or central routes module)
- [X] T020 [US1] Implement `POST /podcast/{id}/archive` behavior: set `PodcastFeed.archive=true`, enqueue episodes with `archive_status='none'` in `app/services/archive_queue.py`
- [X] T021 [US1] Update `GET /podcast/{id}` rendering to show archive button/badges/links in `app/templates/podcasts/detail.html`
- [X] T022 [US1] Ensure completed episode links are safe and use a controlled route (no direct filesystem path exposure) in `app/api/routes/podcast_site.py` (or the file-serving route module used by the app)

**Checkpoint**: US1 complete — enabling archive downloads and UI reflects status

---

## Phase 4: User Story 2 - Manter o arquivo sincronizado (Priority: P2)

**Goal**: With archive enabled, new/unarchived episodes are periodically queued without duplicates.

**Independent Test**: With an archived podcast, mark a new episode as `archive_status='none'` and confirm the periodic sync enqueues it once.

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Unit tests for scheduler enqueue logic (no duplicates) in `tests/unit/test_archive_scheduler.py`
- [X] T024 [P] [US2] Integration test: scheduler enqueues `none` episodes for archived podcasts in `tests/integration/test_archive_sync.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement `archive_sync` job logic (DB query + enqueue) in `app/services/archive_scheduler.py`
- [X] T026 [US2] Ensure scheduler is started/stopped exactly once per process in `app/main.py` (or the existing lifespan module)

**Checkpoint**: US2 complete — periodic job keeps archive synced

---

## Phase 5: User Story 3 - Desativar e limpar arquivamento (Priority: P3)

**Goal**: User can disable archive; queued items are canceled; downloaded files are deleted safely; episode statuses reset.

**Independent Test**: Disable archive and confirm queued becomes `none`, done files are removed from disk, and DB fields reset.

### Tests for User Story 3 ⚠️

- [X] T027 [P] [US3] Contract tests for `DELETE /podcast/{id}/archive` in `tests/contract/test_podcast_archive_site.py`
- [X] T028 [P] [US3] Unit tests for cleanup confinement (never deletes outside `ARCHIVE_DIR`) in `tests/unit/test_archive_cleanup.py`
- [X] T029 [P] [US3] Integration test: disable archive cancels + deletes local files in `tests/integration/test_podcast_archive_disable.py`

### Implementation for User Story 3

- [X] T030 [US3] Add `DELETE /podcast/{id}/archive` route (auth required) in `app/api/routes/podcast_archive_site.py`
- [X] T031 [US3] Implement disable flow: set `PodcastFeed.archive=false`, cancel queued, delete done files, reset fields in `app/services/archive_cleanup.py`
- [X] T032 [US3] Add confirmation UI for destructive disable action in `app/templates/podcasts/detail.html`

**Checkpoint**: US3 complete — archive can be safely disabled and cleaned up

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Ship readiness, docs, and verification evidence

- [X] T033 [P] Document environment variables in `.env.example` (`ARCHIVE_DIR`, `ARCHIVE_WORKERS`, `ARCHIVE_SYNC_INTERVAL_MINUTES`)
- [X] T034 Update `docker-compose.yml` to mount archive volume (`./archive:/app/archive`)
- [X] T035 Add/adjust UI copy for archive statuses in all supported locales in `app/core/localization.py`
- [ ] T036 Run full verification (`uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy app/ tests/`, `uv run bandit -r app -c pyproject.toml`) and capture results in PR description
- [ ] T037 Prepare PR summary referencing `specs/029-podcast-archive/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational completion; proceed in priority order (P1 → P2 → P3) or in parallel if staffed
- **Polish (Phase 6)**: Depends on all targeted stories being complete

### User Story Dependencies

- **US1 (P1)**: Requires Phase 2 only
- **US2 (P2)**: Requires Phase 2; builds on queue + scheduler but should not block US1 once queue exists
- **US3 (P3)**: Requires Phase 2; touches cleanup + disable flow

---

## Parallel Example: User Story 1

```bash
# Tests can be written in parallel:
Task: "Unit tests for slugify + confinement helpers in tests/unit/test_archive_paths.py"
Task: "Unit tests for idempotent enqueue behavior in tests/unit/test_archive_queue.py"
Task: "Contract tests for POST /podcast/{id}/archive in tests/contract/test_podcast_archive_site.py"

# Foundational helpers can be done in parallel:
Task: "Implement archive path helpers in app/services/archive_paths.py"
Task: "Implement safe cleanup in app/services/archive_cleanup.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup + Foundational
2. Complete US1 tests → implement US1
3. Validate US1 independently via `specs/029-podcast-archive/quickstart.md`

### Incremental Delivery

1. Add US2 scheduler sync
2. Add US3 disable + cleanup
3. Final polish + full verification
