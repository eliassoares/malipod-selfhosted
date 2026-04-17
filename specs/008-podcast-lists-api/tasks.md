# Tasks: Podcast Lists API

**Input**: Design documents from `/specs/008-podcast-lists-api/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include tasks for the verification required by the constitution and
feature spec. Because this feature introduces new persistence, format-aware
reads, and authenticated CRUD behavior, add explicit automated and manual
validation tasks for generated-name behavior, list rendering, ownership checks,
and create/update/delete flows.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Application code**: `app/`
- **Database and migrations**: `app/db/`, `alembic/`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **Documentation/configuration**: project root files plus `specs/008-podcast-lists-api/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the podcast-lists workspace, developer verification path, and API route entry points before implementation begins

- [X] T001 Confirm the active branch is `008-podcast-lists-api` and the feature directory in `./.specify/feature.json` points to `specs/008-podcast-lists-api`
- [X] T002 Review and update podcast-lists verification shortcuts in `./Makefile` and `./pyproject.toml`
- [X] T003 [P] Review local environment and manual validation prerequisites for podcast lists in `./.env.example` and `specs/008-podcast-lists-api/quickstart.md`
- [X] T004 [P] Review API router registration points and current compatibility route layout in `app/main.py` and `app/api/routes/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared persistence, schema, format, validation, and dependency foundation required before any podcast-list story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create the `PodcastList` and `PodcastListItem` ORM models plus feed relationships in `app/db/models/podcast.py` and `app/db/models/user.py`
- [X] T006 Update ORM exports and metadata wiring for the podcast-lists domain in `app/db/models/__init__.py` and `app/db/base.py`
- [X] T007 Create the Alembic migration for podcast-list tables in `alembic/versions/0006_podcast_lists.py`
- [X] T008 [P] Add shared podcast-list request and response schemas in `app/schemas/podcast_list.py` and export them from `app/schemas/__init__.py`
- [X] T009 [P] Add canonical-name, list-format, and shared feed URL validation helpers in `app/core/security.py`
- [X] T010 [P] Extend dependency wiring for podcast-list services in `app/api/deps.py`
- [X] T011 [P] Extend shared JSON, OPML, and plaintext parsing/rendering utilities for podcast-list documents in `app/services/subscription_formats.py`
- [X] T012 Implement shared podcast-list persistence, feed resolution, canonical-name generation, and ordering scaffolding in `app/services/podcast_lists.py`
- [X] T013 Register the podcast-lists API router in `app/api/routes/lists_api.py`, `app/api/routes/__init__.py`, `app/services/__init__.py`, and `app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Browse and Read Podcast Lists (Priority: P1) 🎯 MVP

**Goal**: Deliver public list-summary reads and per-list retrieval in supported formats with deterministic ordering and `404` handling for unknown users or lists

**Independent Test**: A client can request `/api/2/lists/{username}.json` and `/api/2/lists/{username}/list/{listname}.{format}` for an existing user, receive the expected summary and ordered list content, and see `404 Not Found` for unknown users or missing list names

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Create contract tests for `GET /api/2/lists/{username}.json` and `GET /api/2/lists/{username}/list/{listname}.{format}` in `tests/contract/test_lists_api.py`
- [X] T015 [P] [US1] Create unit tests for summary ordering, web URL derivation, and list document rendering in `tests/unit/test_podcast_list_service.py`
- [X] T016 [P] [US1] Create integration tests for summary reads, per-list reads, and `404` missing-resource behavior in `tests/integration/test_lists_api_flow.py`

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement user-scoped list summary queries and public web URL serialization in `app/services/podcast_lists.py`
- [X] T018 [P] [US1] Implement per-list read queries and supported-format rendering in `app/services/podcast_lists.py` and `app/services/subscription_formats.py`
- [X] T019 [P] [US1] Implement `GET /api/2/lists/{username}.json` and `GET /api/2/lists/{username}/list/{listname}.{format}` in `app/api/routes/lists_api.py`
- [X] T020 [US1] Integrate public read schemas, not-found handling, and response serialization across `app/services/podcast_lists.py`, `app/schemas/podcast_list.py`, and `app/api/routes/lists_api.py`
- [X] T021 [US1] Document manual verification for list-summary and per-list read flows in `specs/008-podcast-lists-api/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Create a Podcast List (Priority: P1)

**Goal**: Deliver authenticated list creation with format-aware input parsing, deterministic canonical-name generation, conflict detection, and `303 See Other` redirects

**Independent Test**: An authenticated user can submit a title plus list content to `POST /api/2/lists/{username}/create.{format}`, receive a `303` with a `Location` header for the new list, and see `409 Conflict` or authorization failures when the generated name already exists or the requested username is not theirs

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T022 [P] [US2] Extend contract coverage for `POST /api/2/lists/{username}/create.{format}` in `tests/contract/test_lists_api.py`
- [X] T023 [P] [US2] Add unit tests for canonical-name generation, fallback slug behavior, feed normalization, and duplicate-name conflict detection in `tests/unit/test_podcast_list_service.py`
- [X] T024 [P] [US2] Add integration tests for successful creation, `303` redirect responses, and cross-account rejection in `tests/integration/test_lists_api_flow.py`

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement create-document parsing and ordered feed normalization in `app/services/subscription_formats.py` and `app/services/podcast_lists.py`
- [X] T026 [P] [US2] Implement canonical-name generation, conflict checks, feed upsert, and list creation in `app/services/podcast_lists.py`
- [X] T027 [P] [US2] Implement `POST /api/2/lists/{username}/create.{format}` in `app/api/routes/lists_api.py`
- [X] T028 [US2] Integrate redirect response handling, ownership enforcement, and create request validation across `app/services/podcast_lists.py`, `app/schemas/podcast_list.py`, `app/core/security.py`, and `app/api/routes/lists_api.py`
- [X] T029 [US2] Document manual verification for create success, conflict, and ownership rejection in `specs/008-podcast-lists-api/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Maintain an Existing Podcast List (Priority: P2)

**Goal**: Deliver authenticated list replacement and deletion with format-aware updates, deterministic item reordering, and correct `204` or `404` responses

**Independent Test**: An authenticated user can replace or delete one owned list using the documented endpoints, receive `204 No Content`, and see `404 Not Found` or authorization failures when the list is missing or belongs to another user

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T030 [P] [US3] Extend contract coverage for `PUT /api/2/lists/{username}/list/{listname}.{format}` and `DELETE /api/2/lists/{username}/list/{listname}.{format}` in `tests/contract/test_lists_api.py`
- [X] T031 [P] [US3] Add unit tests for ordered list-item replacement, empty-list updates, and delete semantics in `tests/unit/test_podcast_list_service.py`
- [X] T032 [P] [US3] Add integration tests for update, delete, repeated delete, and missing-list flows in `tests/integration/test_lists_api_flow.py`

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement list replacement logic, stable item reordering, and update timestamps in `app/services/podcast_lists.py`
- [X] T034 [P] [US3] Implement list deletion and missing-resource detection in `app/services/podcast_lists.py`
- [X] T035 [P] [US3] Implement `PUT /api/2/lists/{username}/list/{listname}.{format}` and `DELETE /api/2/lists/{username}/list/{listname}.{format}` in `app/api/routes/lists_api.py`
- [X] T036 [US3] Integrate `204` empty responses, ownership enforcement, and format-aware update validation across `app/services/podcast_lists.py`, `app/schemas/podcast_list.py`, and `app/api/routes/lists_api.py`
- [X] T037 [US3] Document manual verification for update, delete, and missing-list behavior in `specs/008-podcast-lists-api/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish contract alignment, full verification, and review readiness across all podcast-list stories

- [X] T038 [P] Align implemented behavior with `specs/008-podcast-lists-api/contracts/podcast-lists-api.openapi.yaml`
- [X] T039 [P] Add any remaining podcast-lists verification required by the constitution in `tests/contract/test_lists_api.py`, `tests/integration/test_lists_api_flow.py`, and `tests/unit/test_podcast_list_service.py`
- [X] T040 [P] Remove or refactor any podcast-lists-related inline suppressions encountered while implementing the feature in `app/` and `tests/`
- [X] T041 Update developer verification shortcuts and feature notes in `./Makefile`, `./README.md`, and `specs/008-podcast-lists-api/quickstart.md`
- [X] T042 Run and document the full podcast-lists quickstart validation in `specs/008-podcast-lists-api/quickstart.md`
- [X] T043 Prepare PR summary with implemented scope, verification evidence, migration notes, and deferred follow-ups in `./PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 and can proceed in parallel after the foundation is ready
  - US3 depends on the same foundation and benefits from list creation and read behavior established in US1 and US2, so the recommended order is US1 → US2 → US3
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and delivers the first usable public list discovery and read contracts
- **User Story 2 (P1)**: Starts after Foundational, depends on shared list persistence and format utilities, and remains independently testable from update/delete behavior
- **User Story 3 (P2)**: Starts after Foundational and depends on the list aggregate established earlier, while remaining independently verifiable once a list exists

### Within Each User Story

- Verification tasks MUST be defined before implementation and tests MUST fail
  before implementation when tests are part of the plan
- Commits MUST follow Conventional Commits throughout the branch history
- Tasks that address lint, typing, or security findings MUST prefer fixing root
  causes over adding `# noqa`, `# nosec`, or similar inline suppressions
- Schemas and parsing rules before service behavior
- Services before routes
- Core implementation before quickstart/manual validation updates
- Story complete before moving to the next priority when delivering incrementally

### Parallel Opportunities

- T003 and T004 can run in parallel during setup
- T008 through T011 can run in parallel during the foundational phase
- T014, T015, and T016 can run in parallel for US1
- T017, T018, and T019 can run in parallel for US1 before T020-T021
- T022, T023, and T024 can run in parallel for US2
- T025, T026, and T027 can run in parallel for US2 before T028-T029
- T030, T031, and T032 can run in parallel for US3
- T033, T034, and T035 can run in parallel for US3 before T036-T037
- T038 through T040 can run in parallel during polish

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 verification work together:
Task: "Create contract tests for GET /api/2/lists/{username}.json and GET /api/2/lists/{username}/list/{listname}.{format} in tests/contract/test_lists_api.py"
Task: "Create unit tests for summary ordering, web URL derivation, and list document rendering in tests/unit/test_podcast_list_service.py"
Task: "Create integration tests for summary reads, per-list reads, and 404 missing-resource behavior in tests/integration/test_lists_api_flow.py"

# Launch User Story 1 implementation work together:
Task: "Implement user-scoped list summary queries and public web URL serialization in app/services/podcast_lists.py"
Task: "Implement per-list read queries and supported-format rendering in app/services/podcast_lists.py and app/services/subscription_formats.py"
Task: "Implement GET /api/2/lists/{username}.json and GET /api/2/lists/{username}/list/{listname}.{format} in app/api/routes/lists_api.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch User Story 2 verification work together:
Task: "Extend contract coverage for POST /api/2/lists/{username}/create.{format} in tests/contract/test_lists_api.py"
Task: "Add unit tests for canonical-name generation, fallback slug behavior, feed normalization, and duplicate-name conflict detection in tests/unit/test_podcast_list_service.py"
Task: "Add integration tests for successful creation, 303 redirect responses, and cross-account rejection in tests/integration/test_lists_api_flow.py"

# Launch User Story 2 implementation work together:
Task: "Implement create-document parsing and ordered feed normalization in app/services/subscription_formats.py and app/services/podcast_lists.py"
Task: "Implement canonical-name generation, conflict checks, feed upsert, and list creation in app/services/podcast_lists.py"
Task: "Implement POST /api/2/lists/{username}/create.{format} in app/api/routes/lists_api.py"
```

---

## Parallel Example: User Story 3

```bash
# Launch User Story 3 verification work together:
Task: "Extend contract coverage for PUT /api/2/lists/{username}/list/{listname}.{format} and DELETE /api/2/lists/{username}/list/{listname}.{format} in tests/contract/test_lists_api.py"
Task: "Add unit tests for ordered list-item replacement, empty-list updates, and delete semantics in tests/unit/test_podcast_list_service.py"
Task: "Add integration tests for update, delete, repeated delete, and missing-list flows in tests/integration/test_lists_api_flow.py"

# Launch User Story 3 implementation work together:
Task: "Implement list replacement logic, stable item reordering, and update timestamps in app/services/podcast_lists.py"
Task: "Implement list deletion and missing-resource detection in app/services/podcast_lists.py"
Task: "Implement PUT /api/2/lists/{username}/list/{listname}.{format} and DELETE /api/2/lists/{username}/list/{listname}.{format} in app/api/routes/lists_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm list-summary reads, per-list reads in supported formats, and `404` behavior for unknown users or lists
5. Demo the public read contracts before adding authenticated create and maintenance behavior

### Incremental Delivery

1. Complete Setup + Foundational -> foundation ready
2. Add User Story 1 -> validate summary reads, ordered list rendering, and missing-resource behavior
3. Add User Story 2 -> validate create redirects, generated-name conflicts, and ownership checks
4. Add User Story 3 -> validate update, delete, and repeated missing-list behavior
5. Finish Polish -> run full quickstart validation and prepare PR summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 public reads and format rendering
   - Developer B: User Story 2 list creation, canonical-name generation, and redirect behavior
   - Developer C: User Story 3 update/delete maintenance flows
3. Rejoin for contract alignment, migration verification, and full quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] labels map tasks back to specific user stories for traceability
- Every user story includes an independent test target
- All tasks include explicit file paths
- Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Format validation: all tasks follow the required `- [X] T### [P] [US#] Description with file path` structure where applicable
