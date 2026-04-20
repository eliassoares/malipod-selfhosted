# Tasks: Client Parametrization

**Input**: Design documents from `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/`
**Prerequisites**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/plan.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/spec.md`

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Confirm working branch is `012-client-parametrization` and clean baseline in `/Users/eliassoares/Documents/projects/personal/malipod/` (`git status`)
- [x] T002 Review contract in `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/contracts/clientconfig-json.md` and align on response fields

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 Identify where the service reads runtime settings in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/deps.py` and confirm `Settings.base_url` source in `/Users/eliassoares/Documents/projects/personal/malipod/app/core/config.py`

**Checkpoint**: Can build response using settings only (no DB access).

---

## Phase 3: User Story 1 - Auto-configurar cliente a partir do servidor (Priority: P1) 🎯 MVP

**Goal**: Expose `GET /clientconfig.json` publicly and return normalized `mygpo.baseurl`.

**Independent Test**: `GET /clientconfig.json` without auth returns `200`, JSON has `mygpo.baseurl` ending with `/` and matching configured server base URL.

### Tests (contract)

- [x] T004 [P] [US1] Add contract test for `GET /clientconfig.json` in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_client_config.py`

### Implementation

- [x] T005 [P] [US1] Add response schema(s) for client config in `/Users/eliassoares/Documents/projects/personal/malipod/app/schemas/client_config.py`
- [x] T006 [P] [US1] Add router for `GET /clientconfig.json` in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/client_config.py` (public, stateless; uses runtime settings; normalizes trailing slash)
- [x] T007 [US1] Wire router into app in `/Users/eliassoares/Documents/projects/personal/malipod/app/main.py`
- [x] T008 [US1] Ensure endpoint returns `application/json` even without `Accept` header (verify via `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_client_config.py`)

**Checkpoint**: User Story 1 passes its contract test; no authentication required; no DB reads/writes.

---

## Phase 4: User Story 2 - Indicar validade da configuração ao cliente (Priority: P2)

**Goal**: Include `update_timeout` (positive integer, seconds) in response.

**Independent Test**: `GET /clientconfig.json` returns `update_timeout` and it is a positive integer.

### Tests (contract)

- [x] T009 [P] [US2] Extend `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_client_config.py` to assert `update_timeout` exists and is a positive integer

### Implementation

- [x] T010 [US2] Add `update_timeout` to response generation in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/client_config.py` (fixed constant; no new settings)

**Checkpoint**: User Story 2 passes; response includes `update_timeout`.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T011 [P] Update quickstart in `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/quickstart.md` if manual verification steps need adjustment
- [x] T012 Run full verification (`make check` and `make test`) and fix any Ruff/MyPy/Bandit findings without `# noqa` / `# nosec` in `/Users/eliassoares/Documents/projects/personal/malipod/`
- [x] T013 Prepare PR summary update in `/Users/eliassoares/Documents/projects/personal/malipod/PR_SUMMARY.md` (contract + verification evidence)

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → (US1) → (US2) → Polish
- US2 depends on US1 (it extends the same endpoint contract).

## Parallel Opportunities

- [P] tasks can run in parallel when they touch different files:
  - T004 and T005 (test + schema)
  - T005 and T006 (schema + router)
  - T009 can be done while implementing T010, after US1 baseline is merged in the branch
