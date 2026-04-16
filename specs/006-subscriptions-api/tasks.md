# Tasks: Subscriptions API

**Input**: Design documents from `/specs/006-subscriptions-api/`
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
- **Documentation/configuration**: project root files plus `specs/006-subscriptions-api/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the branch, verification entry points, and documentation targets for the subscriptions feature

- [X] T001 Confirm the active branch is `006-subscriptions-api` and the feature directory in `./.specify/feature.json` points to `specs/006-subscriptions-api`
- [X] T002 Review and update subscriptions-focused verification shortcuts in `./Makefile` and `./pyproject.toml`
- [X] T003 [P] Review local environment and manual validation prerequisites for subscriptions in `./.env.example` and `specs/006-subscriptions-api/quickstart.md`
- [X] T004 [P] Review API router registration points and current compatibility route layout in `app/main.py` and `app/api/routes/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared persistence, schema, parser, and dependency foundation required before any subscriptions story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create the subscription change-history ORM model and relationship wiring in `app/db/models/podcast.py` and `app/db/models/device.py`
- [X] T006 Update ORM exports and metadata imports for the subscriptions domain in `app/db/models/__init__.py` and `app/db/base.py`
- [X] T007 Create the Alembic migration for subscription sync history in `alembic/versions/0004_subscription_sync_history.py`
- [X] T008 [P] Add shared subscriptions request and response schemas in `app/schemas/subscription.py`
- [X] T009 [P] Add shared format, JSONP, and `since` validation helpers in `app/core/security.py`
- [X] T010 [P] Extend dependency wiring for subscriptions services in `app/api/deps.py`
- [X] T011 Implement shared OPML, JSON, and plaintext parsing/rendering helpers in `app/services/subscription_formats.py`
- [X] T012 Implement shared subscription persistence, normalization, and query scaffolding in `app/services/subscriptions.py`
- [X] T013 Register the subscriptions API router in `app/api/routes/subscriptions_api.py` and `app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Read Account and Device Subscriptions (Priority: P1) 🎯 MVP

**Goal**: Deliver authenticated device-level and account-wide subscription exports in supported formats with deterministic ordering and ownership checks

**Independent Test**: An authenticated client can retrieve a known device or account-wide subscription set in JSON, OPML, and plaintext formats, while unsupported formats and unknown devices return the documented errors

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Create contract tests for `GET /subscriptions/{username}.{format}` and `GET /subscriptions/{username}/{deviceid}.{format}` in `tests/contract/test_subscriptions_api.py`
- [X] T015 [P] [US1] Create unit tests for export ordering, de-duplication, and JSONP/format rendering in `tests/unit/test_subscription_formats.py`
- [X] T016 [P] [US1] Create integration tests for device and account subscription reads in `tests/integration/test_subscriptions_sync_api.py`

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement device-scoped and account-wide read queries in `app/services/subscriptions.py`
- [X] T018 [P] [US1] Implement `GET /subscriptions/{username}.{format}` and `GET /subscriptions/{username}/{deviceid}.{format}` in `app/api/routes/subscriptions_api.py`
- [X] T019 [US1] Integrate format negotiation, JSONP response wrapping, invalid-format handling, and `404` unknown-device behavior across `app/services/subscription_formats.py`, `app/services/subscriptions.py`, `app/schemas/subscription.py`, and `app/api/routes/subscriptions_api.py`
- [X] T020 [US1] Document manual verification for account and device subscription reads in `specs/006-subscriptions-api/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Replace a Device Subscription List (Priority: P1)

**Goal**: Deliver full-device subscription uploads in all supported formats with replacement semantics, auto-created devices, and empty-body success responses

**Independent Test**: An authenticated client can upload a full device subscription list in JSON, OPML, or plaintext, receive `200 OK` with an empty body, and observe that a missing device is created automatically for the targeted account

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T021 [P] [US2] Extend contract coverage for `PUT /subscriptions/{username}/{deviceid}.{format}` in `tests/contract/test_subscriptions_api.py`
- [X] T022 [P] [US2] Add unit tests for full-upload parsing, replacement diffing, duplicate collapse, and auto-created device behavior in `tests/unit/test_subscription_service.py`
- [X] T023 [P] [US2] Add integration tests for full-device upload flows and empty-body responses in `tests/integration/test_subscriptions_sync_api.py`

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement full-upload parsing and normalized input handling in `app/services/subscription_formats.py`
- [X] T025 [P] [US2] Implement full-device replacement, auto-create-device logic, and change-event emission in `app/services/subscriptions.py`
- [X] T026 [P] [US2] Implement `PUT /subscriptions/{username}/{deviceid}.{format}` in `app/api/routes/subscriptions_api.py`
- [X] T027 [US2] Integrate empty-body success responses, cross-account rejection, and device upsert coordination across `app/services/subscriptions.py`, `app/services/devices.py`, and `app/api/routes/subscriptions_api.py`
- [X] T028 [US2] Document manual verification for full uploads and auto-created devices in `specs/006-subscriptions-api/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sync Subscription Changes Incrementally (Priority: P2)

**Goal**: Deliver delta upload and delta read contracts with URL sanitation, conflict rejection, server-issued timestamps, and `since` filtering

**Independent Test**: An authenticated client can upload add/remove deltas, receive a timestamp plus `update_urls`, and then request changes since an earlier timestamp to receive only newer add/remove events

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T029 [P] [US3] Extend contract coverage for `POST /api/2/subscriptions/{username}/{deviceid}.json` and `GET /api/2/subscriptions/{username}/{deviceid}.json` in `tests/contract/test_subscriptions_api.py`
- [X] T030 [P] [US3] Add unit tests for URL sanitation, add/remove conflict rejection, timestamp issuance, and `since` filtering in `tests/unit/test_subscription_service.py`
- [X] T031 [P] [US3] Add integration tests for delta upload/read sync flows, empty changesets, and invalid-device handling in `tests/integration/test_subscriptions_sync_api.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement delta upload normalization, URL rewrite reporting, and conflict detection in `app/services/subscriptions.py`
- [X] T033 [P] [US3] Implement delta history reads and `since` filtering in `app/services/subscriptions.py`
- [X] T034 [P] [US3] Implement `POST /api/2/subscriptions/{username}/{deviceid}.json` and `GET /api/2/subscriptions/{username}/{deviceid}.json` in `app/api/routes/subscriptions_api.py`
- [X] T035 [US3] Integrate server-issued timestamp responses, empty-change handling, and shared validation across `app/services/subscriptions.py`, `app/schemas/subscription.py`, `app/core/security.py`, and `app/api/routes/subscriptions_api.py`
- [X] T036 [US3] Document manual verification for incremental subscription sync in `specs/006-subscriptions-api/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish contract alignment, full verification, and review readiness across all subscriptions stories

- [X] T037 [P] Align implemented behavior with `specs/006-subscriptions-api/contracts/subscriptions-api.openapi.yaml`
- [X] T038 [P] Add any remaining subscriptions verification required by the constitution in `tests/contract/test_subscriptions_api.py`, `tests/integration/test_subscriptions_sync_api.py`, and `tests/unit/test_subscription_service.py`
- [X] T039 [P] Remove or refactor any subscriptions-related inline suppressions encountered while implementing the feature in `app/` and `tests/`
- [X] T040 Update developer verification shortcuts and feature notes in `./Makefile`, `./README.md`, and `specs/006-subscriptions-api/quickstart.md`
- [X] T041 Run and document the full subscriptions quickstart validation in `specs/006-subscriptions-api/quickstart.md`
- [X] T042 Prepare PR summary with implemented scope, verification evidence, migration notes, and deferred follow-ups in `./PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel once the foundation is ready
  - US3 depends on the same foundation and benefits from the replacement/history behavior delivered in US2, so the recommended order is US1 → US2 → US3
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and delivers the first usable bootstrap read contracts for account and device subscriptions
- **User Story 2 (P1)**: Starts after Foundational, depends on shared parsers and persistence scaffolding, and remains independently testable from delta sync
- **User Story 3 (P2)**: Starts after Foundational and depends on the shared change-history and replacement logic established earlier, while remaining independently verifiable once seed data exists

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
- T017 and T018 can run in parallel for US1 before T019-T020
- T021, T022, and T023 can run in parallel for US2
- T024 through T026 can run in parallel for US2 before T027-T028
- T029, T030, and T031 can run in parallel for US3
- T032 through T034 can run in parallel for US3 before T035-T036
- T037 through T039 can run in parallel during polish

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 verification work together:
Task: "Create contract tests for GET /subscriptions/{username}.{format} and GET /subscriptions/{username}/{deviceid}.{format} in tests/contract/test_subscriptions_api.py"
Task: "Create unit tests for export ordering, de-duplication, and JSONP/format rendering in tests/unit/test_subscription_formats.py"
Task: "Create integration tests for device and account subscription reads in tests/integration/test_subscriptions_sync_api.py"

# Launch User Story 1 endpoint work together:
Task: "Implement device-scoped and account-wide read queries in app/services/subscriptions.py"
Task: "Implement GET /subscriptions/{username}.{format} and GET /subscriptions/{username}/{deviceid}.{format} in app/api/routes/subscriptions_api.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch User Story 2 verification work together:
Task: "Extend contract coverage for PUT /subscriptions/{username}/{deviceid}.{format} in tests/contract/test_subscriptions_api.py"
Task: "Add unit tests for full-upload parsing, replacement diffing, duplicate collapse, and auto-created device behavior in tests/unit/test_subscription_service.py"
Task: "Add integration tests for full-device upload flows and empty-body responses in tests/integration/test_subscriptions_sync_api.py"

# Launch User Story 2 implementation work together:
Task: "Implement full-upload parsing and normalized input handling in app/services/subscription_formats.py"
Task: "Implement full-device replacement, auto-create-device logic, and change-event emission in app/services/subscriptions.py"
Task: "Implement PUT /subscriptions/{username}/{deviceid}.{format} in app/api/routes/subscriptions_api.py"
```

---

## Parallel Example: User Story 3

```bash
# Launch User Story 3 verification work together:
Task: "Extend contract coverage for POST /api/2/subscriptions/{username}/{deviceid}.json and GET /api/2/subscriptions/{username}/{deviceid}.json in tests/contract/test_subscriptions_api.py"
Task: "Add unit tests for URL sanitation, add/remove conflict rejection, timestamp issuance, and since filtering in tests/unit/test_subscription_service.py"
Task: "Add integration tests for delta upload/read sync flows, empty changesets, and invalid-device handling in tests/integration/test_subscriptions_sync_api.py"

# Launch User Story 3 endpoint work together:
Task: "Implement delta upload normalization, URL rewrite reporting, and conflict detection in app/services/subscriptions.py"
Task: "Implement POST /api/2/subscriptions/{username}/{deviceid}.json and GET /api/2/subscriptions/{username}/{deviceid}.json in app/api/routes/subscriptions_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm device and account subscription reads in JSON, OPML, and plaintext, plus invalid-format and invalid-device behavior
5. Demo the bootstrap read contracts before adding upload and delta sync behavior

### Incremental Delivery

1. Complete Setup + Foundational -> foundation ready
2. Add User Story 1 -> validate bootstrap reads and deterministic output
3. Add User Story 2 -> validate full uploads, empty-body success, and auto-created devices
4. Add User Story 3 -> validate delta upload/read, URL rewrite reporting, and `since` filtering
5. Finish Polish -> run full quickstart validation and prepare PR summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 read contracts and export formatting
   - Developer B: User Story 2 full upload and replacement behavior
   - Developer C: User Story 3 delta sync and history filtering
3. Rejoin for contract alignment, migration verification, and full quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] labels map tasks back to specific user stories for traceability
- Every user story includes an independent test target
- All tasks include explicit file paths
- Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Format validation: all tasks follow the required `- [ ] T### [P] [US#] Description with file path` structure where applicable
