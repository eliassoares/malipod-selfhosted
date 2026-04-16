# Tasks: Episodes API

**Input**: Design documents from `/specs/007-episodes-api/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include tasks for the verification required by the constitution and
feature spec. Because this feature changes sync behavior and persistence, add
explicit automated and manual validation tasks for upload, retrieval, filters,
aggregation, and compatibility with the existing device updates flow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Application code**: `app/`
- **Database and migrations**: `app/db/`, `alembic/`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **Documentation/configuration**: project root files plus `specs/007-episodes-api/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the episodes feature workspace, verification shortcuts, and route entry points before implementation starts

- [X] T001 Confirm the active branch is `007-episodes-api` and the feature directory in `./.specify/feature.json` points to `specs/007-episodes-api`
- [X] T002 Review and update episode-focused verification shortcuts in `./Makefile` and `./pyproject.toml`
- [X] T003 [P] Review local environment and manual validation prerequisites for episode sync in `./.env.example` and `specs/007-episodes-api/quickstart.md`
- [X] T004 [P] Review API router registration points and current compatibility route layout in `app/main.py` and `app/api/routes/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared persistence, schema, validation, and dependency foundation required before any episodes story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create the append-only episode action history ORM model and relationship wiring in `app/db/models/podcast.py`
- [X] T006 Update ORM exports and metadata imports for the episodes domain in `app/db/models/__init__.py` and `app/db/base.py`
- [X] T007 Create the Alembic migration for episode action history in `alembic/versions/0005_episode_action_history.py`
- [X] T008 [P] Add shared episode action request and response schemas in `app/schemas/episode.py` and export them from `app/schemas/__init__.py`
- [X] T009 [P] Add episode URL sanitization, action-type, playback-progress, and query validation helpers in `app/core/security.py`
- [X] T010 [P] Extend dependency wiring for episode services in `app/api/deps.py`
- [X] T011 Implement shared episode-action persistence, projection refresh, and query scaffolding in `app/services/episodes.py`
- [X] T012 Register the episodes API router in `app/api/routes/episodes_api.py`, `app/api/routes/__init__.py`, `app/services/__init__.py`, and `app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload Episode Actions (Priority: P1) 🎯 MVP

**Goal**: Deliver authenticated batch uploads for episode actions with strict validation, URL sanitation, server-issued timestamps, and latest-state projection updates

**Independent Test**: An authenticated client can upload valid `download`, `play`, `delete`, `new`, and `flattr` actions, receive a numeric `timestamp` plus `update_urls`, and see invalid `play` payloads or malformed URLs handled according to the contract

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Create contract tests for `POST /api/2/episodes/{username}.json` in `tests/contract/test_episodes_api.py`
- [X] T014 [P] [US1] Create unit tests for action validation, URL sanitation, `update_urls`, and projection refresh behavior in `tests/unit/test_episode_service.py`
- [X] T015 [P] [US1] Create integration tests for mixed upload batches, invalid `play` payloads, and sanitized URL handling in `tests/integration/test_episodes_sync_api.py`

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement upload normalization, URL rewrite tracking, and append-only event creation in `app/services/episodes.py`
- [X] T017 [P] [US1] Implement latest-state projection updates for accepted uploads in `app/services/episodes.py` and `app/db/models/podcast.py`
- [X] T018 [P] [US1] Implement the `POST /api/2/episodes/{username}.json` route in `app/api/routes/episodes_api.py`
- [X] T019 [US1] Integrate upload response serialization, ownership enforcement, and validation error handling across `app/services/episodes.py`, `app/schemas/episode.py`, `app/core/security.py`, and `app/api/routes/episodes_api.py`
- [X] T020 [US1] Document manual verification for episode-action uploads in `specs/007-episodes-api/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Retrieve Episode Actions Incrementally (Priority: P1)

**Goal**: Deliver authenticated retrieval of episode action history with deterministic ordering, fresh timestamps, and `since`-based incremental sync behavior

**Independent Test**: An authenticated client can retrieve all stored episode actions, store the returned timestamp, call the same endpoint again with `since`, and receive only newer actions plus a fresh response timestamp

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T021 [P] [US2] Extend contract coverage for `GET /api/2/episodes/{username}.json` basic retrieval and `since` behavior in `tests/contract/test_episodes_api.py`
- [X] T022 [P] [US2] Add unit tests for timestamp issuance, chronological ordering, and `since` filtering in `tests/unit/test_episode_service.py`
- [X] T023 [P] [US2] Add integration tests for initial retrieval, incremental retrieval, and empty-result responses in `tests/integration/test_episodes_sync_api.py`

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement episode action history reads, response ordering, and fresh timestamp issuance in `app/services/episodes.py`
- [X] T025 [P] [US2] Implement the `GET /api/2/episodes/{username}.json` route for unfiltered retrieval in `app/api/routes/episodes_api.py`
- [X] T026 [US2] Integrate `since` parsing, empty-history responses, and response action serialization across `app/services/episodes.py`, `app/schemas/episode.py`, and `app/api/routes/episodes_api.py`
- [X] T027 [US2] Document manual verification for full and incremental episode retrieval in `specs/007-episodes-api/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Filter and Aggregate Episode Actions (Priority: P2)

**Goal**: Deliver podcast and device filters plus `aggregated=true` retrieval that returns only the latest matching action per episode

**Independent Test**: An authenticated client can filter action history by podcast URL or device ID and can request `aggregated=true` to collapse the matching result set to the latest action per episode without leaking cross-account data

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T028 [P] [US3] Extend contract coverage for `podcast`, `device`, and `aggregated` query parameters in `tests/contract/test_episodes_api.py`
- [X] T029 [P] [US3] Add unit tests for podcast filtering, device filtering, aggregation semantics, and deterministic aggregated ordering in `tests/unit/test_episode_service.py`
- [X] T030 [P] [US3] Add integration tests for podcast-filtered, device-filtered, and aggregated retrieval flows in `tests/integration/test_episodes_sync_api.py`

### Implementation for User Story 3

- [X] T031 [P] [US3] Implement podcast and device query filtering in `app/services/episodes.py`
- [X] T032 [P] [US3] Implement `aggregated=true` latest-matching-action reads in `app/services/episodes.py`
- [X] T033 [P] [US3] Extend the `GET /api/2/episodes/{username}.json` route to support filter and aggregation parameters in `app/api/routes/episodes_api.py`
- [X] T034 [US3] Integrate query validation, aggregation serialization, and cross-account filter safety across `app/services/episodes.py`, `app/schemas/episode.py`, `app/core/security.py`, and `app/api/routes/episodes_api.py`
- [X] T035 [US3] Document manual verification for filtered and aggregated episode retrieval in `specs/007-episodes-api/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish contract alignment, compatibility verification, and review readiness across all episodes stories

- [X] T036 [P] Align implemented behavior with `specs/007-episodes-api/contracts/episodes-api.openapi.yaml`
- [X] T037 [P] Add any remaining episodes verification required by the constitution in `tests/contract/test_episodes_api.py`, `tests/integration/test_episodes_sync_api.py`, and `tests/unit/test_episode_service.py`
- [X] T038 [P] Verify that device updates remain compatible with the refreshed latest-state projection in `tests/integration/test_device_updates_api.py` and `tests/unit/test_device_service.py`
- [X] T039 [P] Remove or refactor any episodes-related inline suppressions encountered while implementing the feature in `app/` and `tests/`
- [X] T040 Update developer verification shortcuts and feature notes in `./Makefile`, `./README.md`, and `specs/007-episodes-api/quickstart.md`
- [X] T041 Run and document the full episodes quickstart validation in `specs/007-episodes-api/quickstart.md`
- [X] T042 Prepare PR summary with implemented scope, verification evidence, migration notes, compatibility notes, and deferred follow-ups in `./PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 are both P1, but the recommended order is US1 → US2 because retrieval relies on upload-generated history
  - US3 depends on the same foundation and on seeded history from US1/US2 to validate filters and aggregation
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and delivers the first usable episodes contract for uploading action history
- **User Story 2 (P1)**: Starts after Foundational, benefits from US1 seed data, and remains independently testable once history exists
- **User Story 3 (P2)**: Starts after Foundational and depends on the retrieval shape established in US2 while remaining independently verifiable with seeded action history

### Within Each User Story

- Verification tasks MUST be defined before implementation and tests MUST fail
  before implementation when tests are part of the plan
- Commits MUST follow Conventional Commits throughout the branch history
- Tasks that address lint, typing, or security findings MUST prefer fixing root
  causes over adding `# noqa`, `# nosec`, or similar inline suppressions
- Schemas and validation rules before service behavior
- Services before routes
- Core implementation before quickstart/manual validation updates
- Story complete before moving to the next priority when delivering incrementally

### Parallel Opportunities

- T003 and T004 can run in parallel during setup
- T008 through T010 can run in parallel during the foundational phase
- T013, T014, and T015 can run in parallel for US1
- T016, T017, and T018 can run in parallel for US1 before T019-T020
- T021, T022, and T023 can run in parallel for US2
- T024 and T025 can run in parallel for US2 before T026-T027
- T028, T029, and T030 can run in parallel for US3
- T031, T032, and T033 can run in parallel for US3 before T034-T035
- T036 through T039 can run in parallel during polish

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 verification work together:
Task: "Create contract tests for POST /api/2/episodes/{username}.json in tests/contract/test_episodes_api.py"
Task: "Create unit tests for action validation, URL sanitation, update_urls, and projection refresh behavior in tests/unit/test_episode_service.py"
Task: "Create integration tests for mixed upload batches, invalid play payloads, and sanitized URL handling in tests/integration/test_episodes_sync_api.py"

# Launch User Story 1 endpoint work together:
Task: "Implement upload normalization, URL rewrite tracking, and append-only event creation in app/services/episodes.py"
Task: "Implement latest-state projection updates for accepted uploads in app/services/episodes.py and app/db/models/podcast.py"
Task: "Implement the POST /api/2/episodes/{username}.json route in app/api/routes/episodes_api.py"
```

---

## Parallel Example: User Story 3

```bash
# Launch User Story 3 verification work together:
Task: "Extend contract coverage for podcast, device, and aggregated query parameters in tests/contract/test_episodes_api.py"
Task: "Add unit tests for podcast filtering, device filtering, aggregation semantics, and deterministic aggregated ordering in tests/unit/test_episode_service.py"
Task: "Add integration tests for podcast-filtered, device-filtered, and aggregated retrieval flows in tests/integration/test_episodes_sync_api.py"

# Launch User Story 3 implementation work together:
Task: "Implement podcast and device query filtering in app/services/episodes.py"
Task: "Implement aggregated=true latest-matching-action reads in app/services/episodes.py"
Task: "Extend the GET /api/2/episodes/{username}.json route to support filter and aggregation parameters in app/api/routes/episodes_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm upload batches, `play` validation, URL sanitation, and `timestamp` plus `update_urls` behavior all match the contract
5. Demo the upload contract before adding retrieval and aggregation behavior

### Incremental Delivery

1. Complete Setup + Foundational -> foundation ready
2. Add User Story 1 -> validate uploads, URL rewriting, and latest-state projection refresh
3. Add User Story 2 -> validate full history reads, empty responses, and `since`-based sync
4. Add User Story 3 -> validate podcast/device filters and `aggregated=true`
5. Finish Polish -> run full quickstart validation and prepare PR summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 upload validation and append-only history
   - Developer B: User Story 2 retrieval and `since` synchronization
   - Developer C: User Story 3 filters and aggregation behavior
3. Rejoin for contract alignment, compatibility verification with device updates, and quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] labels map tasks back to specific user stories for traceability
- Every user story includes an independent test target
- All tasks include explicit file paths
- Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Format validation: all tasks follow the required `- [ ] T### [P] [US#] Description with file path` structure where applicable
