# Tasks: Podcast Sync Platform Foundation

**Input**: Design documents from `/specs/003-podcast-sync-platform/`
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
- **Infrastructure**: `docker/`, `alembic/`, `.github/`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **Documentation/configuration**: project root files plus `specs/003-podcast-sync-platform/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the initial project skeleton, dependency baseline, and local execution entry points

- [X] T001 Create feature branch from `main` and confirm branch name matches the feature in `.specify/feature.json`
- [X] T002 Define pinned runtime dependencies and test/runtime groups in `./pyproject.toml`
- [X] T003 [P] Create Docker application image and runtime entrypoint in `docker/app/Dockerfile`
- [X] T004 [P] Create Docker Compose stack for app and PostgreSQL in `./docker-compose.yml`
- [X] T005 [P] Add environment template and startup configuration notes in `./.env.example`
- [X] T006 [P] Add project automation targets for run, test, and container workflows in `./Makefile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core application, configuration, database, and verification plumbing that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create FastAPI app bootstrap and router registration in `app/main.py`
- [X] T008 [P] Implement validated application settings in `app/core/config.py`
- [X] T009 [P] Implement structured logging setup in `app/core/logging.py`
- [X] T010 [P] Implement base security helpers and secret validation in `app/core/security.py`
- [X] T011 [P] Create SQLAlchemy base metadata and shared ORM utilities in `app/db/base.py`
- [X] T012 [P] Implement async runtime/test database session management in `app/db/session.py`
- [X] T013 Create Alembic configuration and initial migration wiring in `alembic/env.py`
- [X] T014 [P] Implement readiness service and probe evaluation model in `app/services/readiness.py`
- [X] T015 [P] Create response schemas for API root and health endpoints in `app/schemas/health.py`
- [X] T016 [P] Create shared site view schema in `app/schemas/site.py`
- [X] T017 Create test infrastructure for async app clients and isolated database contexts in `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Start the Platform Reliably (Priority: P1) 🎯 MVP

**Goal**: Deliver a working FastAPI foundation with both site and API surfaces, safe startup validation, and containerized local execution

**Independent Test**: A maintainer can start the stack from a clean checkout, open the home page, call the API root and health endpoints, and see actionable failure output when configuration is invalid

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T018 [P] [US1] Create contract tests for `/api/v1`, `/api/v1/health/live`, and `/api/v1/health/ready` in `tests/contract/test_foundation_api.py`
- [X] T019 [P] [US1] Create integration tests for app startup and invalid configuration failure handling in `tests/integration/test_app_startup.py`
- [X] T020 [P] [US1] Create integration tests for the rendered home page in `tests/integration/test_site_home.py`

### Implementation for User Story 1

- [X] T021 [P] [US1] Implement API health and root routes in `app/api/routes/health.py`
- [X] T022 [P] [US1] Implement site route handlers in `app/api/routes/site.py`
- [X] T023 [P] [US1] Implement shared dependency helpers for route wiring in `app/api/deps.py`
- [X] T024 [P] [US1] Create the initial server-rendered home page template in `app/templates/home.html`
- [X] T025 [US1] Integrate settings validation, logging, routers, and readiness checks in `app/main.py`
- [X] T026 [US1] Document the startup flow and surface verification steps in `./README.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Work With Safe Environment Boundaries (Priority: P2)

**Goal**: Isolate verification data from runtime data and document the contributor workflow for safe local testing

**Independent Test**: A maintainer can run the automated suite against SQLite-backed test storage without modifying the PostgreSQL-backed development environment

### Tests for User Story 2 ⚠️

- [X] T027 [P] [US2] Create unit tests for runtime/test settings separation in `tests/unit/test_config.py`
- [X] T028 [P] [US2] Create unit and integration tests for readiness behavior with isolated test contexts in `tests/unit/test_readiness.py`

### Implementation for User Story 2

- [X] T029 [P] [US2] Add data-context aware settings and database selection logic in `app/core/config.py`
- [X] T030 [US2] Implement runtime/test engine switching and SQLite isolation behavior in `app/db/session.py`
- [X] T031 [US2] Update test fixtures to enforce isolated database lifecycle management in `tests/conftest.py`
- [X] T032 [US2] Document contributor verification and isolation steps in `specs/003-podcast-sync-platform/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Extend the Product Safely (Priority: P3)

**Goal**: Enforce reproducible dependencies, local quality gates, and review readiness so later sync work starts from a safe baseline

**Independent Test**: A contributor can install the project, run the documented checks, use compliant commit messages, and prepare a PR summary with verification evidence

### Tests for User Story 3 ⚠️

- [X] T033 [P] [US3] Create unit tests for the commit message validator in `tests/unit/test_conventional_commit.py`

### Implementation for User Story 3

- [X] T034 [US3] Finalize local verification and security workflow entries in `./.pre-commit-config.yaml`
- [X] T035 [US3] Update automation targets for local quality, audit, and commit-msg hook installation in `./Makefile`
- [X] T036 [US3] Implement and refine Conventional Commit validation in `scripts/check_conventional_commit.py`
- [X] T037 [US3] Update the PR template with scope, verification, and follow-up requirements in `./.github/PULL_REQUEST_TEMPLATE.md`
- [X] T038 [US3] Document dependency pinning and review expectations in `./README.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish cross-story infrastructure, migrations, and end-to-end verification

- [X] T039 [P] Add ORM models for operational foundation entities in `app/db/models/foundation.py`
- [X] T040 Create the initial Alembic migration for foundation tables in `alembic/versions/0001_foundation_tables.py`
- [X] T041 [P] Align the implemented API behavior with `specs/003-podcast-sync-platform/contracts/foundation-api.openapi.yaml`
- [X] T042 [P] Add any remaining unit/integration assertions needed by the constitution in `tests/unit/` and `tests/integration/`
- [X] T043 Run and document full quickstart validation in `specs/003-podcast-sync-platform/quickstart.md`
- [X] T044 Prepare PR summary with implemented scope, verification evidence, and follow-ups in `./PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel if desired, though US2 and US3 both benefit from the app skeleton delivered in US1
  - Recommended sequence is P1 → P2 → P3
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational - establishes the executable MVP
- **User Story 2 (P2)**: Starts after Foundational - builds on the runtime/test plumbing and verifies isolation
- **User Story 3 (P3)**: Starts after Foundational - can proceed independently of US2, but should land after or alongside US1 so contributor workflows reflect the implemented app

### Within Each User Story

- Verification tasks MUST be defined before implementation and tests MUST fail before implementation when tests are part of the plan
- Commits MUST follow Conventional Commits throughout the branch history
- Schemas and low-level helpers before route/service integration
- Runtime wiring before documentation of the finished workflow
- Story complete before moving to the next priority if delivering incrementally

### Parallel Opportunities

- T003, T004, T005, and T006 can run in parallel during setup
- T008 through T012 and T014 through T016 can run in parallel once the app skeleton direction is fixed
- T018, T019, and T020 can run in parallel for US1
- T021 through T024 can run in parallel for US1 after the tests are written
- T027 and T028 can run in parallel for US2
- T033 and T037 can run in parallel for US3
- T039, T041, and T042 can run in parallel during polish

---

## Parallel Example: User Story 1

```bash
# Launch US1 test work together:
Task: "Create contract tests for /api/v1, /api/v1/health/live, and /api/v1/health/ready in tests/contract/test_foundation_api.py"
Task: "Create integration tests for app startup and invalid configuration failure handling in tests/integration/test_app_startup.py"
Task: "Create integration tests for the rendered home page in tests/integration/test_site_home.py"

# Launch US1 implementation work together:
Task: "Implement API health and root routes in app/api/routes/health.py"
Task: "Implement site route handlers in app/api/routes/site.py"
Task: "Create the initial server-rendered home page template in app/templates/home.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run startup, site, API, and invalid-config verification for the MVP
5. Share/demo the foundation before adding isolation and workflow refinements

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → validate startup and both product surfaces
3. Add User Story 2 → validate isolated verification and safe data boundaries
4. Add User Story 3 → validate contribution workflow, pinned dependencies, and review readiness
5. Finish Polish → run end-to-end quickstart validation and prepare PR summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 application surfaces
   - Developer B: User Story 2 test isolation and verification plumbing
   - Developer C: User Story 3 contributor workflow and governance
3. Rejoin for polish, migration alignment, and quickstart verification

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] labels map tasks back to specific user stories for traceability
- Every user story includes an independent test target
- All tasks include explicit file paths
- Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Format validation: all tasks use the required `- [ ] T### [P] [US#] Description with file path` structure where applicable
