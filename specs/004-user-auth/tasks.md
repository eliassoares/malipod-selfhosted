# Tasks: User Authentication and Localized Profile

**Input**: Design documents from `/specs/004-user-auth/`
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
- **Templates**: `app/templates/`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/contract/`
- **Documentation/configuration**: project root files plus `specs/004-user-auth/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the auth feature workspace, shared dependencies, and local verification entry points

- [X] T001 Confirm the active branch is `004-user-auth` and the feature directory in `./.specify/feature.json` points to `specs/004-user-auth`
- [X] T002 Review and update pinned dependencies and tool configuration for the auth feature in `./pyproject.toml`
- [X] T003 [P] Update local environment documentation for auth- and session-related settings in `./.env.example`
- [X] T004 [P] Extend automation targets for auth-focused verification workflows in `./Makefile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core account, session, localization, and routing infrastructure that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create shared user and session ORM models in `app/db/models/user.py` and `app/db/models/session.py`
- [X] T006 Create the Alembic migration for user and session tables in `alembic/versions/0002_user_auth_entities.py`
- [X] T007 [P] Add account and session schemas for form/API payloads in `app/schemas/auth.py`
- [X] T008 [P] Add profile page schemas in `app/schemas/profile.py`
- [X] T009 [P] Implement password derivation, credential verification, nickname validation, and session token helpers in `app/core/security.py`
- [X] T010 [P] Implement supported-locale definitions and locale resolution helpers in `app/core/localization.py`
- [X] T011 Implement auth and locale-aware database/service helpers in `app/api/deps.py`
- [X] T012 Implement account/session persistence and query helpers in `app/services/auth.py`
- [X] T013 [P] Implement localization and cookie synchronization service helpers in `app/services/localization.py`
- [X] T014 Wire auth, localization, and session configuration into `app/core/config.py`
- [X] T015 Register new auth/profile routers and shared template context in `app/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create an Account From the Website (Priority: P1) 🎯 MVP

**Goal**: Deliver a website registration flow that creates valid accounts, rejects duplicates, and works on both mobile and desktop layouts

**Independent Test**: A visitor can open the registration page, submit valid account data, create an account, and receive clear validation errors for duplicate accounts or invalid nicknames without using the API directly

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T016 [P] [US1] Create unit tests for nickname, language, and registration validation rules in `tests/unit/test_user_validation.py`
- [X] T017 [P] [US1] Create integration tests for the website registration flow in `tests/integration/test_auth_pages.py`

### Implementation for User Story 1

- [X] T018 [P] [US1] Implement the website registration route handlers in `app/api/routes/auth_site.py`
- [X] T019 [P] [US1] Create the shared auth base layout and reusable partials in `app/templates/base.html`, `app/templates/partials/head.html`, `app/templates/partials/topbar.html`, and `app/templates/partials/footer.html`
- [X] T020 [US1] Implement the responsive registration page in `app/templates/auth/register.html`
- [X] T021 [US1] Integrate account creation, duplicate-user rejection, and timestamp updates in `app/services/auth.py`
- [X] T022 [US1] Document the website registration verification flow in `specs/004-user-auth/quickstart.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sign In and Sign Out Across Web and API (Priority: P1)

**Goal**: Deliver website and API login/logout flows with shared server-side sessions, generic invalid-login responses, and API contract compatibility

**Independent Test**: An existing user can sign in from the website, sign in and sign out through the compatibility API contract, receive a persisted session cookie, and get only the generic invalid-login message when credentials are wrong

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US2] Create contract tests for the compatibility login/logout endpoints in `tests/contract/test_auth_api.py`
- [X] T024 [P] [US2] Create unit tests for password verification and session lifecycle behavior in `tests/unit/test_auth_service.py`
- [X] T025 [P] [US2] Create integration tests for website login/logout and session reuse in `tests/integration/test_auth_sessions.py`

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement the compatibility API login/logout routes in `app/api/routes/auth_api.py`
- [X] T027 [P] [US2] Extend the website auth routes for login/logout behavior in `app/api/routes/auth_site.py`
- [X] T028 [US2] Implement the responsive login page in `app/templates/auth/login.html`
- [X] T029 [US2] Implement session creation, validation, revocation, and generic invalid-login behavior in `app/services/auth.py`
- [X] T030 [US2] Integrate cookie issuance, cookie mismatch handling, and redirect behavior in `app/api/deps.py` and `app/main.py`
- [X] T031 [US2] Document API and website login/logout verification in `specs/004-user-auth/quickstart.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Use a Localized Profile Experience (Priority: P2)

**Goal**: Deliver an authenticated profile page that honors stored language preference, keeps cookie and account locale in sync, and reuses shared layout components

**Independent Test**: A signed-in user can reach `/user/profile/{nickname}`, see the page rendered in the selected supported language, and keep a consistent locale across repeat visits even when an older guest cookie exists

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T032 [P] [US3] Create unit tests for locale precedence and cookie synchronization in `tests/unit/test_localization.py`
- [X] T033 [P] [US3] Create integration tests for localized profile rendering in `tests/integration/test_profile_page.py`

### Implementation for User Story 3

- [X] T034 [P] [US3] Implement the localized profile route handlers in `app/api/routes/profile_site.py`
- [X] T035 [P] [US3] Implement profile page translation and context assembly in `app/services/localization.py` and `app/schemas/profile.py`
- [X] T036 [US3] Implement the responsive localized profile page in `app/templates/profile/detail.html`
- [X] T037 [US3] Finalize language-selection behavior across auth and profile pages in `app/core/localization.py`, `app/api/routes/auth_site.py`, and `app/api/routes/profile_site.py`
- [X] T038 [US3] Document profile and multilingual verification in `specs/004-user-auth/quickstart.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish shared validation, documentation, and end-to-end verification across all stories

- [X] T039 [P] Align the implemented auth responses and cookies with `specs/004-user-auth/contracts/auth-api.openapi.yaml`
- [X] T040 [P] Add any remaining end-to-end assertions required by the constitution in `tests/integration/test_auth_pages.py`, `tests/integration/test_auth_sessions.py`, and `tests/integration/test_profile_page.py`
- [X] T041 [P] Remove or refactor any auth-related inline suppressions encountered while implementing the feature in `app/` and `tests/`
- [X] T042 Run and document full account-flow quickstart validation in `specs/004-user-auth/quickstart.md`
- [X] T043 Prepare PR summary with implemented scope, verification evidence, responsive checks, and deferred follow-ups in `./PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel if needed, though US2 builds naturally on the account entities and services used by US1
  - Recommended order is US1 → US2 → US3
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational and delivers the first public account entry flow
- **User Story 2 (P1)**: Starts after Foundational and depends on the shared account/session infrastructure, but remains independently testable from US3
- **User Story 3 (P2)**: Starts after Foundational and benefits from the authenticated session behavior completed in US2

### Within Each User Story

- Verification tasks MUST be defined before implementation and tests MUST fail
  before implementation when tests are part of the plan
- Commits MUST follow Conventional Commits throughout the branch history
- Tasks that address lint, typing, or security findings MUST prefer fixing root
  causes over adding `# noqa`, `# nosec`, or similar inline suppressions
- Models and schemas before services
- Services before routes and templates
- Core implementation before integration
- Story complete before moving to the next priority when delivering incrementally

### Parallel Opportunities

- T003 and T004 can run in parallel during setup
- T007 through T010 and T013 can run in parallel during the foundational phase
- T016 and T017 can run in parallel for US1
- T018 and T019 can run in parallel for US1 before T020-T022
- T023, T024, and T025 can run in parallel for US2
- T026 and T027 can run in parallel for US2 before T028-T031
- T032 and T033 can run in parallel for US3
- T034 and T035 can run in parallel for US3 before T036-T038
- T039, T040, and T041 can run in parallel during polish

---

## Parallel Example: User Story 2

```bash
# Launch User Story 2 verification work together:
Task: "Create contract tests for the compatibility login/logout endpoints in tests/contract/test_auth_api.py"
Task: "Create unit tests for password verification and session lifecycle behavior in tests/unit/test_auth_service.py"
Task: "Create integration tests for website login/logout and session reuse in tests/integration/test_auth_sessions.py"

# Launch User Story 2 route work together:
Task: "Implement the compatibility API login/logout routes in app/api/routes/auth_api.py"
Task: "Extend the website auth routes for login/logout behavior in app/api/routes/auth_site.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Confirm registration works on mobile and desktop, validates nickname rules, and rejects duplicate users
5. Demo the first account entry flow before adding login/logout and profile localization

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → validate registration and duplicate-user handling
3. Add User Story 2 → validate website/API login, session cookies, and logout invalidation
4. Add User Story 3 → validate localized profile rendering and locale precedence
5. Finish Polish → run full quickstart validation and prepare PR summary

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 registration flow and shared auth templates
   - Developer B: User Story 2 API/web authentication and session lifecycle
   - Developer C: User Story 3 localization and profile rendering
3. Rejoin for polish, contract alignment, and quickstart verification

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] labels map tasks back to specific user stories for traceability
- Every user story includes an independent test target
- All tasks include explicit file paths
- Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Format validation: all tasks follow the required `- [ ] T### [P] [US#] Description with file path` structure where applicable
