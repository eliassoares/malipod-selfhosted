# Tasks: Centralized Subscriptions Sync

**Input**: Design documents from `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/`
**Prerequisites**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/plan.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/spec.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/research.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/data-model.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/contracts/subscriptions-api.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/022-centralized-subscriptions-sync/quickstart.md`

**Tests**: Extend contract/integration coverage for subscriptions endpoints in both modes (centralized on/off), including OPML and delta semantics, plus profile toggle persistence tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm scope and locate existing subscription + delta logic.

- [x] T001 Confirm working branch is `022-centralized-subscriptions-sync` and feature directory is `specs/022-centralized-subscriptions-sync/`
- [x] T002 Review current subscriptions read/delta behavior in `app/api/routes/subscriptions_api.py` and `app/services/subscriptions.py` (delta lives in `SubscriptionService.get_changes`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the persisted preference and wire it into user model + profile update flow.

**⚠️ CRITICAL**: No centralized behavior should ship without the flag persisted and tested.

- [x] T003 Add `centralize_sync` field to `UserModel` in `app/db/models/user.py`
- [x] T004 Add Alembic migration for `users.centralize_sync` in `alembic/versions/0015_centralize_sync.py`
- [x] T005 Ensure profile form POST can update `centralize_sync` for current user in `app/api/routes/profile_site.py`
- [x] T006 [P] Add localization keys for profile toggle copy in `app/core/localization.py`
- [x] T007 Add checkbox/toggle UI in profile template in `app/templates/profile/detail.html`
- [x] T008 [P] Add integration test for `centralize_sync` toggle persistence in `tests/integration/test_profile_page.py`

**Checkpoint**: User preference persists, is editable only by the owner, and is translated.

---

## Phase 3: User Story 1 - Ativar/desativar sincronização centralizada (Priority: P1) 🎯 MVP

**Goal**: User can control centralized subscriptions mode from the profile page.

**Independent Test**: Toggle persists and is reflected in subsequent reads (covered by integration test).

### Tests for User Story 1 ⚠️

- [x] T009 [P] [US1] Add integration test that profile toggle is owner-only (cannot update others) in `tests/integration/test_profile_page.py`

### Implementation for User Story 1

- [x] T010 [US1] Enforce owner-only update behavior for `centralize_sync` in `app/api/routes/profile_site.py` (if not already enforced)

**Checkpoint**: US1 tests pass.

---

## Phase 4: User Story 2 - Ler inscrições unificadas via protocolo (Priority: P2)

**Goal**: `GET /api/2/subscriptions/{user}/{device}.json` and `.opml` return device-scoped or centralized union based on `centralize_sync`.

**Independent Test**: With multiple devices subscribed to different feeds, centralized mode returns union; default mode returns per-device subscriptions; OPML matches JSON selection.

### Tests for User Story 2 ⚠️

- [x] T011 [P] [US2] Add contract test for centralized vs device-scoped JSON reads in `tests/contract/test_subscriptions_api.py`
- [x] T012 [P] [US2] Add contract test for centralized vs device-scoped OPML reads in `tests/contract/test_subscriptions_api.py`

### Implementation for User Story 2

- [x] T013 [US2] Update subscriptions listing query to support centralized union in `app/services/subscriptions.py`
- [x] T014 [US2] Pass authenticated user into subscriptions service calls in `app/api/routes/subscriptions_api.py`
- [x] T015 [US2] Ensure OPML rendering uses the same feed selection in `app/api/routes/subscriptions_api.py`

**Checkpoint**: US2 contract tests pass and output shapes remain unchanged.

---

## Phase 5: User Story 3 - Delta changes centralizado (Priority: P3)

**Goal**: Centralized delta semantics for `POST /api/2/subscriptions/{user}/{device}.json`:
- `add`: union across devices since `since`
- `remove`: only if absent from all active subscriptions at read time

**Independent Test**: With multi-device subscriptions, single-device unsubscribe does not show as remove while still subscribed elsewhere; once unsubscribed everywhere, remove appears.

### Tests for User Story 3 ⚠️

- [x] T016 [P] [US3] Add contract tests for centralized delta `add` union semantics in `tests/contract/test_subscriptions_api.py`
- [x] T017 [P] [US3] Add contract tests for centralized delta `remove` filter (“absent from all”) in `tests/contract/test_subscriptions_api.py`

### Implementation for User Story 3

- [x] T018 [US3] Update delta changes service to aggregate across devices when centralized in `app/services/subscriptions.py`
- [x] T019 [US3] Ensure centralized delta remove list is filtered by current active union in `app/services/subscriptions.py`
- [x] T020 [US3] Wire user preference into delta route in `app/api/routes/subscriptions_api.py`

**Checkpoint**: US3 contract tests pass and behavior matches spec.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates and PR readiness.

- [x] T021 Run full quality gates and record evidence in PR summary: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run bandit -r app -c pyproject.toml`, `uv run pip-audit`
- [x] T022 Prepare PR summary including semantics, verification evidence, and follow-ups in `PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → required to locate current logic and avoid regressions.
- **Foundational (Phase 2)** → blocks centralized behavior (flag + UI + persistence).
- **US1 (Phase 3)** → depends on Phase 2; delivers MVP toggle control.
- **US2 (Phase 4)** → depends on Phase 2; read behavior switching.
- **US3 (Phase 5)** → depends on Phase 2; delta semantics.
- **Polish (Phase 6)** → after desired stories complete.

### User Story Dependencies

- **US1 (P1)**: Enables safe control of the feature.
- **US2 (P2)**: Can ship without US3 (read-only centralized).
- **US3 (P3)**: Adds correctness for incremental sync (deltas).

### Parallel Opportunities

- [P] tasks can be run in parallel where files do not overlap (i18n, tests).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. Validate toggle persistence and owner-only behavior

### Incremental Delivery

1. US1 → US2 → US3
2. Finish with Phase 6 quality gates + PR summary
