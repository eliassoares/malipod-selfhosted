# Tasks: Device API

**Input**: Design documents from `/specs/005-device-api/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include tasks for the verification needed by the constitution and
feature spec. If behavior changes, add the relevant automated and manual
validation tasks explicitly.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Application code**: `app/`
- **Database and migrations**: `app/db/`, `alembic/`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **Documentation/configuration**: project root files plus `specs/005-device-api/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the device feature workspace, developer verification path, and API documentation entry points

- [ ] T001 Confirm the active branch is `005-device-api` and the feature directory in `./.specify/feature.json` points to `specs/005-device-api`
- [ ] T002 Review and update pinned tooling or developer shortcuts for device-focused verification in `./pyproject.toml` and `./Makefile`
- [ ] T003 [P] Review environment and local-run documentation for device-sync prerequisites in `./.env.example` and `specs/005-device-api/quickstart.md`
- [ ] T004 [P] Review API router registration points and current route organization in `app/main.py` and `app/api/routes/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core persistence, schema, service, and routing infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create shared device and sync-domain ORM models in `app/db/models/device.py` and `app/db/models/podcast.py`
- [ ] T006 Update ORM model exports and metadata wiring in `app/db/models/__init__.py` and `app/db/base.py`
- [ ] T007 Create the Alembic migration for device and sync entities in `alembic/versions/0003_device_sync_entities.py`
- [ ] T008 [P] Add shared request and response schemas for the Device API in `app/schemas/device.py`
- [ ] T009 [P] Add device ID, timestamp, and supported-type validation helpers in `app/core/security.py`
- [ ] T010 [P] Extend dependency wiring for authenticated device services in `app/api/deps.py`
- [ ] T011 Implement shared device persistence and query helpers in `app/services/devices.py`
- [ ] T012 Register the new device API router in `app/api/routes/devices_api.py` and `app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Register and Update a Device Identity (Priority: P1) 🎯 MVP

**Goal**: Deliver an authenticated contract that creates or partially updates a per-user device record with strict device-ID and ownership validation

**Independent Test**: An authenticated client can create a device with a valid ID, update only one mutable field later, and receive validation or authorization failures for invalid IDs or cross-account requests

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Create unit tests for device ID, caption, and device-type validation in `tests/unit/test_device_service.py`
- [ ] T014 [P] [US1] Create contract tests for `POST /api/2/devices/{username}/{deviceid}.json` in `tests/contract/test_device_api.py`
- [ ] T015 [P] [US1] Create integration tests for authenticated create/update device flows in `tests/integration/test_device_updates_api.py`

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement device create-or-update service behavior in `app/services/devices.py`
- [ ] T017 [P] [US1] Implement the `POST /api/2/devices/{username}/{deviceid}.json` route in `app/api/routes/devices_api.py`
- [ ] T018 [US1] Integrate device timestamp updates, ownership enforcement, and partial-field updates across `app/services/devices.py` and `app/schemas/device.py`
- [ ] T019 [US1] Document manual verification for device registration and partial updates in `specs/005-device-api/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - List Devices for an Account (Priority: P1)

**Goal**: Deliver an authenticated device-list contract that returns only the targeted user's devices with accurate captions, types, and subscription counts

**Independent Test**: An authenticated user can request their device list and receive only their devices, including empty-caption devices and an empty list when no devices exist

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T020 [P] [US2] Extend contract coverage for `GET /api/2/devices/{username}.json` in `tests/contract/test_device_api.py`
- [ ] T021 [P] [US2] Add unit tests for device list serialization and subscription counting in `tests/unit/test_device_service.py`
- [ ] T022 [P] [US2] Add integration tests for populated and empty device-list flows in `tests/integration/test_device_updates_api.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement device list and subscription count queries in `app/services/devices.py`
- [ ] T024 [P] [US2] Implement the `GET /api/2/devices/{username}.json` route in `app/api/routes/devices_api.py`
- [ ] T025 [US2] Integrate device summary serialization and empty-list behavior in `app/schemas/device.py` and `app/services/devices.py`
- [ ] T026 [US2] Document manual verification for device listing behavior in `specs/005-device-api/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Retrieve Device-Specific Updates (Priority: P2)

**Goal**: Deliver an authenticated incremental updates contract that returns add/remove subscription changes, episode updates, `since` filtering, and optional action payloads

**Independent Test**: An authenticated client can call the updates endpoint for a known device, receive a complete initial snapshot, repeat the call with the returned timestamp, and optionally request action payloads for non-`new` episode states

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T027 [P] [US3] Extend contract coverage for `GET /api/2/updates/{username}/{deviceid}.json` in `tests/contract/test_device_api.py`
- [ ] T028 [P] [US3] Add unit tests for timestamp filtering, update assembly, and optional action inclusion in `tests/unit/test_device_service.py`
- [ ] T029 [P] [US3] Add integration tests for initial sync, incremental sync, and missing-device flows in `tests/integration/test_device_updates_api.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement sync snapshot assembly for subscriptions and episode updates in `app/services/devices.py`
- [ ] T031 [P] [US3] Implement the `GET /api/2/updates/{username}/{deviceid}.json` route in `app/api/routes/devices_api.py`
- [ ] T032 [US3] Integrate `since` parsing, unknown-device handling, and `include_actions` support across `app/services/devices.py`, `app/schemas/device.py`, and `app/api/routes/devices_api.py`
- [ ] T033 [US3] Document manual verification for incremental update retrieval in `specs/005-device-api/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish shared verification, contract alignment, and review preparation across all stories

- [ ] T034 [P] Align implemented API behavior with `specs/005-device-api/contracts/device-api.openapi.yaml`
- [ ] T035 [P] Add any remaining device end-to-end assertions required by the constitution in `tests/contract/test_device_api.py`, `tests/integration/test_device_updates_api.py`, and `tests/unit/test_device_service.py`
- [ ] T036 [P] Remove or refactor any device-related inline suppressions encountered while implementing the feature in `app/` and `tests/`
- [ ] T037 Run and document the full Device API quickstart validation in `specs/005-device-api/quickstart.md`
- [ ] T038 Prepare PR summary with implemented scope, verification evidence, migration notes, and deferred sync follow-ups in `./PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel once the foundation is ready
  - US3 depends on the same foundation and benefits from US1/US2 data shape completion, so the recommended order is US1 → US2 → US3
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and delivers the first usable device identity contract
- **User Story 2 (P1)**: Starts after Foundational and depends on shared device persistence, but remains independently testable from US3
- **User Story 3 (P2)**: Starts after Foundational and depends on shared device and sync-domain persistence established earlier, while remaining independently verifiable once its seed data exists

### Within Each User Story

- Verification tasks MUST be defined before implementation and tests MUST fail
  before implementation when tests are part of the plan
- Commits MUST follow Conventional Commits throughout the branch history
- Tasks that address lint, typing, or security findings MUST prefer fixing root
  causes over adding `# noqa`, `# nosec`, or similar inline suppressions
- Models and shared schemas before services
- Services before routes
- Core implementation before integration polish
- Story complete before moving to the next priority when delivering incrementally

### Parallel Opportunities

- T003 and T004 can run in parallel during setup
- T008 through T010 can run in parallel during the foundational phase
- T013, T014, and T015 can run in parallel for US1
- T016 and T017 can run in parallel for US1 before T018-T019
- T020, T021, and T022 can run in parallel for US2
- T023 and T024 can run in parallel for US2 before T025-T026
- T027, T028, and T029 can run in parallel for US3
- T030 and T031 can run in parallel for US3 before T032-T033
- T034, T035, and T036 can run in parallel during polish

---

## Parallel Example: User Story 3

```bash
# Launch User Story 3 verification work together:
Task: "Extend contract coverage for GET /api/2/updates/{username}/{deviceid}.json in tests/contract/test_device_api.py"
Task: "Add unit tests for timestamp filtering, update assembly, and optional action inclusion in tests/unit/test_device_service.py"
Task: "Add integration tests for initial sync, incremental sync, and missing-device flows in tests/integration/test_device_updates_api.py"

# Launch User Story 3 endpoint work together:
Task: "Implement sync snapshot assembly for subscriptions and episode updates in app/services/devices.py"
Task: "Implement the GET /api/2/updates/{username}/{deviceid}.json route in app/api/routes/devices_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm device creation, partial updates, invalid ID rejection, and cross-account denial all behave correctly
5. Demo the device identity contract before adding list and incremental update retrieval

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → validate device registration and partial metadata updates
3. Add User Story 2 → validate account-scoped device listing and subscription counts
4. Add User Story 3 → validate initial sync, incremental sync, and optional action inclusion
5. Finish Polish → run full quickstart validation and prepare PR summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 device registration/update flow
   - Developer B: User Story 2 device listing and count serialization
   - Developer C: User Story 3 update assembly and incremental sync behavior
3. Rejoin for contract alignment, migration verification, and quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] labels map tasks back to specific user stories for traceability
- Every user story includes an independent test target
- All tasks include explicit file paths
- Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Format validation: all tasks follow the required `- [ ] T### [P] [US#] Description with file path` structure where applicable
