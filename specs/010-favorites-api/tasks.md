# Tasks: Favorites API

**Input**: Design documents from `/specs/010-favorites-api/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include tasks for the verification required by the constitution and
feature spec. Because this feature introduces authenticated favorite retrieval,
new persistence, stable ordering, and metadata serialization, add explicit
automated and manual validation tasks for successful reads, empty lists,
authentication failures, cross-account denial, missing-user behavior, duplicate
prevention, and optional metadata handling.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Application code**: `app/`
- **Database and migrations**: `app/db/`, `alembic/`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **Documentation/configuration**: project root files plus `specs/010-favorites-api/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the favorites-api workspace, verification path, and integration points before implementation begins

- [X] T001 Confirm the active branch is `010-favorites-api` and the feature directory in `./.specify/feature.json` points to `specs/010-favorites-api`
- [X] T002 Review favorites-api verification expectations in `specs/010-favorites-api/plan.md`, `specs/010-favorites-api/quickstart.md`, and `specs/010-favorites-api/contracts/favorites-api.openapi.yaml`
- [X] T003 [P] Review current authenticated compatibility route patterns in `app/api/routes/episodes_api.py` and `app/api/routes/subscriptions_api.py`
- [X] T004 [P] Review current episode/feed model relationships and migration conventions in `app/db/models/podcast.py`, `app/db/models/__init__.py`, and `alembic/versions/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared persistence, schema, service, and router foundation required before any user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Add the `FavoriteEpisode` ORM model and relationship wiring in `app/db/models/podcast.py` and `app/db/models/user.py`
- [X] T006 Update ORM exports for favorite persistence in `app/db/models/__init__.py` and `app/db/base.py`
- [X] T007 Create the Alembic migration for `favorite_episodes` in `alembic/versions/0008_favorite_episodes.py`
- [X] T008 [P] Add favorite response schemas and serialization helpers in `app/schemas/favorite.py` and export them from `app/schemas/__init__.py`
- [X] T009 [P] Add dependency wiring for the favorites service in `app/api/deps.py`, `app/services/__init__.py`, and `app/api/routes/__init__.py`
- [X] T010 Implement the shared `FavoritesService` scaffolding for user lookup, favorite queries, and metadata joins in `app/services/favorites.py`
- [X] T011 Register the favorites API router in `app/api/routes/favorites_api.py` and `app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Read My Favorite Episodes (Priority: P1) 🎯 MVP

**Goal**: Deliver authenticated reads for one user's favorite episodes as a JSON array with the documented episode and podcast fields

**Independent Test**: An authenticated user can request `GET /api/2/favorites/{username}.json` for their own account, receive a `200 OK` JSON array containing only their favorites, and receive `[]` when they have no favorites

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Create contract tests for `GET /api/2/favorites/{username}.json` success and empty-list behavior in `tests/contract/test_favorites_api.py`
- [X] T013 [P] [US1] Create unit tests for favorite retrieval, empty responses, and response serialization in `tests/unit/test_favorite_service.py`
- [X] T014 [P] [US1] Create integration tests for authenticated same-user favorite reads and empty responses in `tests/integration/test_favorites_api_flow.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement favorite query loading and same-user retrieval in `app/services/favorites.py`
- [X] T016 [P] [US1] Implement favorite-item response mapping in `app/services/favorites.py` and `app/schemas/favorite.py`
- [X] T017 [P] [US1] Implement authenticated `GET /api/2/favorites/{username}.json` in `app/api/routes/favorites_api.py`
- [X] T018 [US1] Integrate empty-array handling and success response serialization across `app/services/favorites.py`, `app/schemas/favorite.py`, and `app/api/routes/favorites_api.py`
- [X] T019 [US1] Document manual happy-path and empty-list validation in `specs/010-favorites-api/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Preserve Favorite Episode Metadata (Priority: P2)

**Goal**: Preserve stable ordering and complete favorite item metadata so clients can render favorites without additional lookups

**Independent Test**: A client can retrieve multiple favorites and verify deterministic ordering plus the expected title, URL, podcast, description, website, released timestamp, and public link fields, including null-compatible optional values

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T020 [P] [US2] Extend contract coverage for metadata fields and null-compatible optional values in `tests/contract/test_favorites_api.py`
- [X] T021 [P] [US2] Add unit tests for stable ordering, duplicate prevention semantics, and optional metadata serialization in `tests/unit/test_favorite_service.py`
- [X] T022 [P] [US2] Add integration tests for multi-favorite ordering and partially populated metadata in `tests/integration/test_favorites_api_flow.py`

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement deterministic ordering by `favorited_at` descending and `episode_id` ascending in `app/services/favorites.py`
- [X] T024 [P] [US2] Implement optional metadata normalization for `description`, `website`, `released`, and `mygpo_link` in `app/services/favorites.py` and `app/schemas/favorite.py`
- [X] T025 [P] [US2] Enforce duplicate-prevention constraints and query assumptions in `app/db/models/podcast.py`, `alembic/versions/0008_favorite_episodes.py`, and `app/services/favorites.py`
- [X] T026 [US2] Refine schema and service integration so favorite responses preserve all documented podcast and episode metadata in `app/schemas/favorite.py` and `app/services/favorites.py`
- [X] T027 [US2] Document ordering and optional-metadata manual validation in `specs/010-favorites-api/quickstart.md`

**Checkpoint**: At this point, User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Protect Favorite Episode Access (Priority: P2)

**Goal**: Enforce authentication, account ownership, and missing-user behavior so favorites remain private to the owning account

**Independent Test**: Requests without authentication, with another user's credentials, or for a missing username are rejected with the documented HTTP responses and never expose favorite data

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T028 [P] [US3] Extend contract coverage for `401`, `403`, and `404` responses in `tests/contract/test_favorites_api.py`
- [X] T029 [P] [US3] Add unit tests for username ownership checks and missing-user handling in `tests/unit/test_favorite_service.py`
- [X] T030 [P] [US3] Add integration tests for missing-auth, cross-account denial, and unknown-user reads in `tests/integration/test_favorites_api_flow.py`

### Implementation for User Story 3

- [X] T031 [P] [US3] Implement missing-user detection and ownership validation in `app/services/favorites.py`
- [X] T032 [P] [US3] Implement route-level translation for `401`, `403`, and `404` favorites responses in `app/api/routes/favorites_api.py`
- [X] T033 [P] [US3] Reuse authenticated dependency flow for favorites access in `app/api/deps.py` and `app/api/routes/favorites_api.py`
- [X] T034 [US3] Ensure unauthorized and cross-account reads return no favorite payload data across `app/services/favorites.py` and `app/api/routes/favorites_api.py`
- [X] T035 [US3] Document manual auth-failure, cross-account, and missing-user validation in `specs/010-favorites-api/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish repository-wide verification, cleanup, and review preparation

- [X] T036 [P] Add startup and router registration coverage for the favorites API in `tests/integration/test_app_startup.py`
- [X] T037 [P] Run repository quality gates and record the commands/results in `specs/010-favorites-api/quickstart.md`
- [X] T038 Run the full favorites quickstart validation and capture any final documentation refinements in `specs/010-favorites-api/quickstart.md`
- [X] T039 Prepare PR summary with implemented scope, verification evidence, migration notes, and deferred follow-ups in `./PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 should be delivered first because it provides the MVP favorites read contract
  - US2 builds on the same retrieval path to harden metadata mapping and deterministic ordering
  - US3 builds on the shared retrieval path to finish access protection and error semantics
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and delivers the first usable authenticated favorites read contract
- **User Story 2 (P2)**: Starts after Foundational and can build on the same service/query foundation while remaining independently testable from auth edge cases
- **User Story 3 (P2)**: Starts after Foundational and hardens the same endpoint with ownership and missing-user protections

### Within Each User Story

- Verification tasks MUST be defined before implementation and tests MUST fail
  before implementation when tests are part of the plan
- Commits MUST follow Conventional Commits throughout the branch history
- Tasks that address lint, typing, or security findings MUST prefer fixing root
  causes over adding `# noqa`, `# nosec`, or similar inline suppressions
- Models and schemas before service refinements
- Services before routes
- Core implementation before quickstart/manual validation updates
- Story complete before moving to the next priority when delivering incrementally

### Parallel Opportunities

- T003 and T004 can run in parallel during setup
- T008 and T009 can run in parallel during the foundational phase
- T012, T013, and T014 can run in parallel for US1
- T015, T016, and T017 can run in parallel for US1 before T018-T019
- T020, T021, and T022 can run in parallel for US2
- T023, T024, and T025 can run in parallel for US2 before T026-T027
- T028, T029, and T030 can run in parallel for US3
- T031, T032, and T033 can run in parallel for US3 before T034-T035
- T036 and T037 can run in parallel during polish

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 verification work together:
Task: "Create contract tests for GET /api/2/favorites/{username}.json success and empty-list behavior in tests/contract/test_favorites_api.py"
Task: "Create unit tests for favorite retrieval, empty responses, and response serialization in tests/unit/test_favorite_service.py"
Task: "Create integration tests for authenticated same-user favorite reads and empty responses in tests/integration/test_favorites_api_flow.py"

# Launch User Story 1 implementation work together:
Task: "Implement favorite query loading and same-user retrieval in app/services/favorites.py"
Task: "Implement favorite-item response mapping in app/services/favorites.py and app/schemas/favorite.py"
Task: "Implement authenticated GET /api/2/favorites/{username}.json in app/api/routes/favorites_api.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch User Story 2 verification work together:
Task: "Extend contract coverage for metadata fields and null-compatible optional values in tests/contract/test_favorites_api.py"
Task: "Add unit tests for stable ordering, duplicate prevention semantics, and optional metadata serialization in tests/unit/test_favorite_service.py"
Task: "Add integration tests for multi-favorite ordering and partially populated metadata in tests/integration/test_favorites_api_flow.py"

# Launch User Story 2 implementation work together:
Task: "Implement deterministic ordering by favorited_at descending and episode_id ascending in app/services/favorites.py"
Task: "Implement optional metadata normalization for description, website, released, and mygpo_link in app/services/favorites.py and app/schemas/favorite.py"
Task: "Enforce duplicate-prevention constraints and query assumptions in app/db/models/podcast.py, alembic/versions/0008_favorite_episodes.py, and app/services/favorites.py"
```

---

## Parallel Example: User Story 3

```bash
# Launch User Story 3 verification work together:
Task: "Extend contract coverage for 401, 403, and 404 responses in tests/contract/test_favorites_api.py"
Task: "Add unit tests for username ownership checks and missing-user handling in tests/unit/test_favorite_service.py"
Task: "Add integration tests for missing-auth, cross-account denial, and unknown-user reads in tests/integration/test_favorites_api_flow.py"

# Launch User Story 3 implementation work together:
Task: "Implement missing-user detection and ownership validation in app/services/favorites.py"
Task: "Implement route-level translation for 401, 403, and 404 favorites responses in app/api/routes/favorites_api.py"
Task: "Reuse authenticated dependency flow for favorites access in app/api/deps.py and app/api/routes/favorites_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm authenticated reads for populated and empty favorites responses
5. Demo the read contract before tightening metadata and access edge cases

### Incremental Delivery

1. Complete Setup + Foundational -> foundation ready
2. Add User Story 1 -> validate authenticated favorite reads and empty responses
3. Add User Story 2 -> validate metadata completeness, ordering, and duplicate-prevention semantics
4. Add User Story 3 -> validate unauthorized, cross-account, and missing-user behavior
5. Finish Polish -> run full quickstart validation and prepare PR summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A owns US1 read path and route wiring
   - Developer B owns US2 metadata ordering and serialization refinements
   - Developer C owns US3 auth and error-behavior hardening
3. Rejoin for Phase 6 verification, quickstart validation, and PR preparation
