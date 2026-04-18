# Tasks: Device Synchronization API

**Input**: Design documents from `/specs/011-device-sync-api/`
**Prerequisites**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/011-device-sync-api/plan.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/011-device-sync-api/spec.md`

**Tests**: Include automated verification required by the constitution and the
feature spec (unit + contract + integration) plus minimal manual checks from
quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Every task includes an exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm baseline context and keep spec-kit artifacts consistent

- [x] T001 Confirm current branch is `011-device-sync-api` and that planning artifacts exist under `/Users/eliassoares/Documents/projects/personal/malipod/specs/011-device-sync-api/` (spec.md, plan.md, tasks.md)
- [x] T002 [P] Review `/Users/eliassoares/Documents/projects/personal/malipod/specs/011-device-sync-api/contracts/device-sync-api.openapi.yaml` and confirm it matches the intended endpoint paths and payload shape
- [x] T003 [P] Add a PR summary stub for this feature in `/Users/eliassoares/Documents/projects/personal/malipod/PR_SUMMARY.md` (device-sync section only)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Decide persistence shape for sync groups (device column + group table) and document final decision in `/Users/eliassoares/Documents/projects/personal/malipod/specs/011-device-sync-api/research.md`
- [x] T005 Add ORM model for sync groups in `/Users/eliassoares/Documents/projects/personal/malipod/app/db/models/device_sync_group.py`
- [x] T006 Update existing device model with optional group membership in `/Users/eliassoares/Documents/projects/personal/malipod/app/db/models/device.py`
- [x] T007 Create Alembic migration to add group table + device FK/column in `/Users/eliassoares/Documents/projects/personal/malipod/alembic/versions/0009_device_sync_groups.py`
- [x] T008 [P] Add request/response schemas with correct JSON aliases (`not-synchronized`, `stop-synchronize`) in `/Users/eliassoares/Documents/projects/personal/malipod/app/schemas/sync_devices.py`
- [x] T009 Create service skeleton and typed errors in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/sync_devices.py`
- [x] T010 Wire dependency injection for the new service in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/deps.py`
- [x] T011 Create route module skeleton (router + auth dependency wiring only) in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/sync_devices_api.py`
- [x] T012 Register the new router in `/Users/eliassoares/Documents/projects/personal/malipod/app/main.py`

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 - Consultar status de sincronização (Priority: P1) 🎯 MVP

**Goal**: Usuário autenticado consegue consultar `GET /api/2/sync-devices/{username}.json` e ver grupos sincronizados vs não sincronizados.

**Independent Test**: Com 0 grupos → `synchronized: []` e `not-synchronized` lista todos os devices do usuário; com grupos → `synchronized` contém arrays (2+ ids) e `not-synchronized` contém o resto.

### Tests for User Story 1 ⚠️

- [x] T013 [P] [US1] Add contract tests for GET status shape + auth/403 in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_sync_devices_api.py`
- [x] T014 [P] [US1] Add integration test for GET status with seeded devices in `/Users/eliassoares/Documents/projects/personal/malipod/tests/integration/test_sync_devices_api_flow.py`
- [x] T015 [P] [US1] Add unit tests for status serialization ordering in `/Users/eliassoares/Documents/projects/personal/malipod/tests/unit/test_device_sync_service.py`

### Implementation for User Story 1

- [x] T016 [US1] Implement device-group query + deterministic response ordering in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/sync_devices.py`
- [x] T017 [US1] Implement GET handler returning `SyncDevicesStatus` in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/sync_devices_api.py`
- [x] T018 [US1] Add SQLite test seeding helpers for sync-group state in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_sync_devices_api.py`

**Checkpoint**: US1 works end-to-end (GET only) and tests pass independently

---

## Phase 4: User Story 2 - Iniciar e parar sincronização entre dispositivos (Priority: P2)

**Goal**: Usuário autenticado consegue alterar grupos via POST e recebe status atualizado.

**Independent Test**: POST `{"synchronize":[["a","b"]]}` coloca ambos no mesmo grupo; POST `{"stop-synchronize":["b"]}` remove do grupo; operações repetidas são idempotentes.

### Tests for User Story 2 ⚠️

- [x] T019 [P] [US2] Extend contract tests for POST mutation request/response in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_sync_devices_api.py`
- [x] T020 [P] [US2] Extend integration flow test covering synchronize + stop-synchronize in `/Users/eliassoares/Documents/projects/personal/malipod/tests/integration/test_sync_devices_api_flow.py`
- [x] T021 [P] [US2] Add unit tests for group merge/split/idempotency rules in `/Users/eliassoares/Documents/projects/personal/malipod/tests/unit/test_device_sync_service.py`

### Implementation for User Story 2

- [x] T022 [US2] Implement POST payload validation + normalization (dedupe, validate device IDs) in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/sync_devices.py`
- [x] T023 [US2] Implement mutation semantics (merge groups, detach devices, cleanup groups <2) in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/sync_devices.py`
- [x] T024 [US2] Implement POST handler parsing `SyncDevicesMutation` and returning updated `SyncDevicesStatus` in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/sync_devices_api.py`

**Checkpoint**: US2 works end-to-end (GET + POST) and remains independently testable

---

## Phase 5: User Story 3 - Segurança e mensagens de erro previsíveis (Priority: P3)

**Goal**: Erros comuns (sem auth, cross-account, device inexistente, payload inválido) retornam respostas previsíveis sem mudanças parciais.

**Independent Test**: POST com device inexistente retorna 400 e não altera estado; GET/POST de outro usuário retorna 403; sem auth retorna 401.

### Tests for User Story 3 ⚠️

- [x] T025 [P] [US3] Add tests for invalid payloads, unknown devices, cross-user references, and no-partial-apply semantics in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_sync_devices_api.py`
- [x] T026 [P] [US3] Add integration test ensuring failed POST does not mutate existing groups in `/Users/eliassoares/Documents/projects/personal/malipod/tests/integration/test_sync_devices_api_flow.py`

### Implementation for User Story 3

- [x] T027 [US3] Ensure all referenced devices belong to the authenticated user before applying any mutation in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/sync_devices.py`
- [x] T028 [US3] Map domain errors to consistent HTTP responses (400/401/403/404) in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/sync_devices_api.py`
- [x] T029 [US3] Add minimal logging for denied access and invalid mutation attempts using existing logging approach in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/sync_devices_api.py`

**Checkpoint**: All security/error scenarios are covered by tests and consistent behavior

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, docs alignment, and review readiness

- [x] T030 [P] Validate `/Users/eliassoares/Documents/projects/personal/malipod/specs/011-device-sync-api/quickstart.md` commands still match implemented endpoints and update if needed
- [x] T031 Run repository checks (`uv run ruff check .`, `uv run mypy app tests`, `uv run bandit -r . -c pyproject.toml`, `uv run pip-audit`, `uv run pytest -q`) and record a short verification summary in `/Users/eliassoares/Documents/projects/personal/malipod/PR_SUMMARY.md`
- [x] T032 Prepare PR summary in `/Users/eliassoares/Documents/projects/personal/malipod/PR_SUMMARY.md` with scope, verification evidence, and follow-ups

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup; BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational completion
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational; delivers MVP (GET status)
- **US2 (P2)**: Can start after Foundational; builds on the same endpoint with POST mutation
- **US3 (P3)**: Can start after Foundational; hardens error handling and atomicity

### Parallel Opportunities

- Tests within each user story marked [P] can be developed in parallel.
- Schema work (`app/schemas/sync_devices.py`) and service scaffolding (`app/services/sync_devices.py`) can be developed in parallel during Foundational.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 + Phase 2
2. Implement and validate US1 (GET status)
3. Stop and validate US1 independently via unit/contract/integration tests

### Incremental Delivery

1. Add US2 (POST mutations) and validate idempotent semantics
2. Add US3 hardening and re-run full checks before PR
