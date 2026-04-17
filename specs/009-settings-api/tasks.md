# Tasks: Settings API

**Input**: Design documents from `/specs/009-settings-api/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include tasks for the verification required by the constitution and
feature spec. Because this feature introduces new persistence, authenticated
scope resolution, and arbitrary JSON handling, add explicit automated and
manual validation tasks for reads, writes, validation failures, not-found
behavior, and cross-account protections.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Application code**: `app/`
- **Database and migrations**: `app/db/`, `alembic/`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **Documentation/configuration**: project root files plus `specs/009-settings-api/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the settings-api workspace, verification path, and integration points before implementation begins

- [ ] T001 Confirm the active branch is `009-settings-api` and the feature directory in `./.specify/feature.json` points to `specs/009-settings-api`
- [ ] T002 Review settings-api verification expectations in `specs/009-settings-api/plan.md`, `specs/009-settings-api/quickstart.md`, and `specs/009-settings-api/contracts/settings-api.openapi.yaml`
- [ ] T003 [P] Review current authenticated compatibility route patterns in `app/api/routes/subscriptions_api.py` and `app/api/routes/episodes_api.py`
- [ ] T004 [P] Review current model export and migration conventions in `app/db/models/__init__.py`, `app/db/base.py`, and `alembic/versions/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared persistence, schema, validation, service, and router foundation required before any user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create scoped settings ORM models in `app/db/models/settings.py`
- [ ] T006 Update ORM exports and relationship wiring in `app/db/models/__init__.py`, `app/db/models/user.py`, `app/db/models/device.py`, and `app/db/models/podcast.py`
- [ ] T007 Create the Alembic migration for scoped settings tables in `alembic/versions/0007_settings_api.py`
- [ ] T008 [P] Add shared scope, query, mutation, and response schemas in `app/schemas/setting.py` and export them from `app/schemas/__init__.py`
- [ ] T009 [P] Add settings scope, JSON-object, and target query validation helpers in `app/core/security.py`
- [ ] T010 [P] Add dependency wiring for the settings service in `app/api/deps.py`, `app/services/__init__.py`, and `app/api/routes/__init__.py`
- [ ] T011 Implement the shared `SettingsService` scaffolding for scope resolution and atomic document mutation in `app/services/settings.py`
- [ ] T012 Register the settings API router in `app/api/routes/settings_api.py` and `app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Read Scoped Settings (Priority: P1) 🎯 MVP

**Goal**: Deliver authenticated reads for account, device, podcast, and episode settings with correct scope validation and not-found behavior

**Independent Test**: A client can request `GET /api/2/settings/{username}/{scope}.json` for valid account, device, podcast, and episode targets, receive the current settings object for that exact scope, receive `{}` for valid empty scopes, and see `400`, `401`, `403`, or `404` for invalid or unauthorized requests

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Create contract tests for `GET /api/2/settings/{username}/{scope}.json` in `tests/contract/test_settings_api.py`
- [ ] T014 [P] [US1] Create unit tests for scope query validation and empty-document reads in `tests/unit/test_setting_service.py`
- [ ] T015 [P] [US1] Create integration tests for account, device, podcast, and episode reads plus invalid-target behavior in `tests/integration/test_settings_api_flow.py`

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement account and device scope read resolution in `app/services/settings.py`
- [ ] T017 [P] [US1] Implement podcast and episode scope read resolution in `app/services/settings.py`
- [ ] T018 [P] [US1] Implement authenticated `GET /api/2/settings/{username}/{scope}.json` in `app/api/routes/settings_api.py`
- [ ] T019 [US1] Integrate read response serialization, empty valid scope handling, and domain error mapping across `app/services/settings.py`, `app/schemas/setting.py`, and `app/api/routes/settings_api.py`
- [ ] T020 [US1] Document manual read validation for all four scopes in `specs/009-settings-api/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Save and Remove Scoped Settings (Priority: P1)

**Goal**: Deliver authenticated writes that apply `set` and `remove` atomically and return the resulting settings object for the targeted scope

**Independent Test**: An authenticated user can submit a valid JSON mutation to `POST /api/2/settings/{username}/{scope}.json`, receive the full resulting document for account, device, podcast, and episode scopes, and observe rejected malformed payloads or cross-account attempts without persisted side effects

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T021 [P] [US2] Extend contract coverage for `POST /api/2/settings/{username}/{scope}.json` in `tests/contract/test_settings_api.py`
- [ ] T022 [P] [US2] Add unit tests for atomic `set` and `remove` mutation behavior in `tests/unit/test_setting_service.py`
- [ ] T023 [P] [US2] Add integration tests for successful writes, removals, malformed payloads, and cross-account denial in `tests/integration/test_settings_api_flow.py`

### Implementation for User Story 2

- [ ] T024 [P] [US2] Implement lazy document creation and mutation application for account and device scopes in `app/services/settings.py`
- [ ] T025 [P] [US2] Implement lazy document creation and mutation application for podcast and episode scopes in `app/services/settings.py`
- [ ] T026 [P] [US2] Implement authenticated `POST /api/2/settings/{username}/{scope}.json` in `app/api/routes/settings_api.py`
- [ ] T027 [US2] Integrate request-body validation, atomic transaction boundaries, and resulting-document responses across `app/services/settings.py`, `app/schemas/setting.py`, and `app/api/routes/settings_api.py`
- [ ] T028 [US2] Document manual write and removal validation for all four scopes in `specs/009-settings-api/quickstart.md`

**Checkpoint**: At this point, User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Preserve Scope Rules and Known Settings Semantics (Priority: P2)

**Goal**: Preserve known setting names, arbitrary JSON round-tripping, and strict scope-specific validation semantics across reads and writes

**Independent Test**: A client can store known settings and arbitrary nested JSON values, retrieve them unchanged for the same scope, and observe deterministic `400` or `404` behavior when required identifiers are missing or the referenced target does not exist

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US3] Extend contract tests for scope-specific validation and not-found semantics in `tests/contract/test_settings_api.py`
- [ ] T030 [P] [US3] Add unit tests for known-setting round-tripping, unknown-key retention, and JSON type preservation in `tests/unit/test_setting_service.py`
- [ ] T031 [P] [US3] Add integration tests for nested JSON values, missing query parameters, podcast-episode mismatch, and missing-target `404` behavior in `tests/integration/test_settings_api_flow.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement strict scope-target validation and podcast-episode matching rules in `app/services/settings.py`
- [ ] T033 [P] [US3] Implement schema-level validation for known scopes, required query parameters, and JSON-object payload rules in `app/schemas/setting.py` and `app/core/security.py`
- [ ] T034 [P] [US3] Refine route-level error translation for invalid scope, missing identifiers, and missing targets in `app/api/routes/settings_api.py`
- [ ] T035 [US3] Ensure known settings and arbitrary JSON values round-trip without coercion across `app/services/settings.py`, `app/db/models/settings.py`, and `app/schemas/setting.py`
- [ ] T036 [US3] Document manual validation for known settings, nested JSON values, and scope-rule failures in `specs/009-settings-api/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish repository-wide verification, cleanup, and review preparation

- [ ] T037 [P] Add startup and router registration coverage for the settings API in `tests/integration/test_app_startup.py`
- [ ] T038 [P] Run repository quality gates and record the commands/results in `specs/009-settings-api/quickstart.md`
- [ ] T039 Run the full settings quickstart validation and capture any final documentation refinements in `specs/009-settings-api/quickstart.md`
- [ ] T040 Prepare PR summary with implemented scope, verification evidence, migration notes, and deferred follow-ups in `./PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 and can proceed in parallel after the foundation is ready
  - US3 depends on the same foundation and benefits from the read/write paths established in US1 and US2, so the recommended order is US1 → US2 → US3
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and delivers the first usable authenticated settings read contracts
- **User Story 2 (P1)**: Starts after Foundational, depends on shared scope resolution and persistence scaffolding, and remains independently testable from advanced scope semantics
- **User Story 3 (P2)**: Starts after Foundational and builds on the same settings surface to harden validation, JSON round-tripping, and known-setting compatibility

### Within Each User Story

- Verification tasks MUST be defined before implementation and tests MUST fail
  before implementation when tests are part of the plan
- Commits MUST follow Conventional Commits throughout the branch history
- Tasks that address lint, typing, or security findings MUST prefer fixing root
  causes over adding `# noqa`, `# nosec`, or similar inline suppressions
- Schemas and validation before service refinements
- Services before routes
- Core implementation before quickstart/manual validation updates
- Story complete before moving to the next priority when delivering incrementally

### Parallel Opportunities

- T003 and T004 can run in parallel during setup
- T008 through T010 can run in parallel during the foundational phase
- T013, T014, and T015 can run in parallel for US1
- T016, T017, and T018 can run in parallel for US1 before T019-T020
- T021, T022, and T023 can run in parallel for US2
- T024, T025, and T026 can run in parallel for US2 before T027-T028
- T029, T030, and T031 can run in parallel for US3
- T032, T033, and T034 can run in parallel for US3 before T035-T036
- T037 and T038 can run in parallel during polish

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 verification work together:
Task: "Create contract tests for GET /api/2/settings/{username}/{scope}.json in tests/contract/test_settings_api.py"
Task: "Create unit tests for scope query validation and empty-document reads in tests/unit/test_setting_service.py"
Task: "Create integration tests for account, device, podcast, and episode reads plus invalid-target behavior in tests/integration/test_settings_api_flow.py"

# Launch User Story 1 implementation work together:
Task: "Implement account and device scope read resolution in app/services/settings.py"
Task: "Implement podcast and episode scope read resolution in app/services/settings.py"
Task: "Implement authenticated GET /api/2/settings/{username}/{scope}.json in app/api/routes/settings_api.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch User Story 2 verification work together:
Task: "Extend contract coverage for POST /api/2/settings/{username}/{scope}.json in tests/contract/test_settings_api.py"
Task: "Add unit tests for atomic set and remove mutation behavior in tests/unit/test_setting_service.py"
Task: "Add integration tests for successful writes, removals, malformed payloads, and cross-account denial in tests/integration/test_settings_api_flow.py"

# Launch User Story 2 implementation work together:
Task: "Implement lazy document creation and mutation application for account and device scopes in app/services/settings.py"
Task: "Implement lazy document creation and mutation application for podcast and episode scopes in app/services/settings.py"
Task: "Implement authenticated POST /api/2/settings/{username}/{scope}.json in app/api/routes/settings_api.py"
```

---

## Parallel Example: User Story 3

```bash
# Launch User Story 3 verification work together:
Task: "Extend contract tests for scope-specific validation and not-found semantics in tests/contract/test_settings_api.py"
Task: "Add unit tests for known-setting round-tripping, unknown-key retention, and JSON type preservation in tests/unit/test_setting_service.py"
Task: "Add integration tests for nested JSON values, missing query parameters, podcast-episode mismatch, and missing-target 404 behavior in tests/integration/test_settings_api_flow.py"

# Launch User Story 3 implementation work together:
Task: "Implement strict scope-target validation and podcast-episode matching rules in app/services/settings.py"
Task: "Implement schema-level validation for known scopes, required query parameters, and JSON-object payload rules in app/schemas/setting.py and app/core/security.py"
Task: "Refine route-level error translation for invalid scope, missing identifiers, and missing targets in app/api/routes/settings_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm authenticated reads for account, device, podcast, and episode scopes plus `{}` and `404` behavior
5. Demo the read contracts before adding mutations

### Incremental Delivery

1. Complete Setup + Foundational -> foundation ready
2. Add User Story 1 -> validate authenticated reads and scope-target handling
3. Add User Story 2 -> validate writes, removals, and resulting-document responses
4. Add User Story 3 -> validate strict scope rules, known-setting compatibility, and arbitrary JSON round-tripping
5. Finish Polish -> run full quickstart validation and prepare PR summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 read flows and route integration
   - Developer B: User Story 2 mutation flows and persistence updates
   - Developer C: User Story 3 validation hardening and semantic edge cases
3. Rejoin for startup coverage, quality gates, and full quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] labels map tasks back to specific user stories for traceability
- Every user story includes an independent test target
- All tasks include explicit file paths
- Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Format validation: all tasks follow the required `- [ ] T### [P] [US#] Description with file path` structure where applicable
