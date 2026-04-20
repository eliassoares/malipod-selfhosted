# Tasks: Directory API

**Input**: Design documents from `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/`
**Prerequisites**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/plan.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Confirm working branch is `013-directory-api` and clean baseline in `/Users/eliassoares/Documents/projects/personal/malipod/` (`git status`)
- [x] T002 Review Directory API contracts in `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/contracts/` and align on JSON/OPML/TXT outputs

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 Add shared `count`/`number` validation helper (1–100) in `/Users/eliassoares/Documents/projects/personal/malipod/app/core/security.py` (reused by all Directory endpoints)
- [x] T004 [P] Add Directory API response schemas in `/Users/eliassoares/Documents/projects/personal/malipod/app/schemas/directory.py`
- [x] T005 Add Directory query service skeleton in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/directory.py` (DB read-only queries; subscriber aggregation; mygpo_link builder)
- [x] T006 Add Directory API router skeleton in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/directory_api.py` (public endpoints, parameter parsing, content negotiation)
- [x] T007 Wire Directory router into `/Users/eliassoares/Documents/projects/personal/malipod/app/main.py`

**Checkpoint**: Router + service exist; shared validation is in place; no endpoint writes to DB.

---

## Phase 3: User Story 1 - Buscar podcasts por nome ou URL (Priority: P1) 🎯 MVP

**Goal**: Implement `/search.{json|opml|txt}?q=...` with case-insensitive substring matching and catalog-only results.

**Independent Test**: Seed feeds + active subscriptions; `GET /search.json?q=linux` returns matching feeds; empty results return `[]`; OPML/TXT outputs are valid.

### Tests (contract)

- [x] T008 [P] [US1] Add contract tests for `/search.json`, `/search.opml`, `/search.txt` in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_directory_api.py` (includes empty result case)

### Implementation

- [x] T009 [US1] Implement directory search query in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/directory.py` (catalog-only; title/feed URL matching; limit results safely)
- [x] T010 [US1] Implement `/search.{format}` handler in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/directory_api.py` using `SubscriptionFormatService` for OPML/TXT

**Checkpoint**: US1 passes contract tests; endpoint is public; empty search returns `[]`.

---

## Phase 4: User Story 2 - Consultar toplist de podcasts (Priority: P2)

**Goal**: Implement `/toplist/{number}.{json|opml|txt}` ordered by distinct subscribers desc and limited to `number`.

**Independent Test**: Seed multiple users subscribing to feeds; `/toplist/5.json` returns <= 5 items ordered by subscribers desc; out-of-range returns 400.

### Tests (contract)

- [x] T011 [P] [US2] Add contract tests for `/toplist/{n}.{format}` in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_directory_api.py` (ordering, limit, empty toplist, out-of-range 400)

### Implementation

- [x] T012 [US2] Implement toplist query in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/directory.py` (distinct user count per feed; order desc; limit)
- [x] T013 [US2] Implement `/toplist/{number}.{format}` handler in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/directory_api.py` (validate 1–100; format outputs)

**Checkpoint**: US2 passes contract tests; toplist ordering/limit enforced.

---

## Phase 5: User Story 3 - Consultar tags e podcasts por tag (Priority: P3)

**Goal**: Implement `/api/2/tags/{count}.json` and `/api/2/tag/{tag}/{count}.json` derived from stored feed categories/tags.

**Independent Test**: Seed feeds with stored categories; `/api/2/tags/10.json` returns up to 10 tags with `title`, `tag`, `usage`; tag route returns feeds; missing tag returns `[]`; out-of-range returns 400.

### Tests (contract)

- [x] T014 [P] [US3] Add contract tests for tags endpoints in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_directory_api.py` (limit, empty, out-of-range 400)

### Implementation

- [x] T015 [US3] Ensure feed categories/tags are available locally (update `/Users/eliassoares/Documents/projects/personal/malipod/app/db/models/podcast.py` and any feed upsert flows to persist categories if missing)
- [x] T016 [US3] Implement tag aggregation queries in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/directory.py` (usage count; order by usage desc; limit)
- [x] T017 [US3] Implement tag endpoints in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/directory_api.py`

**Checkpoint**: US3 passes contract tests; tags are derived locally; no new tag table.

---

## Phase 6: User Story 4 - Consultar metadados de podcast ou episódio por URL (Priority: P3)

**Goal**: Implement `/api/2/data/podcast.json?url=...` and `/api/2/data/episode.json?podcast=...&url=...` returning 200 or 404 as specified.

**Independent Test**: Seed feed+episode in catalog; podcast endpoint returns required fields including `subscribers` and server-based `mygpo_link`; unknown URL returns 404; episode endpoint returns fields or 404.

### Tests (contract)

- [x] T018 [P] [US4] Add contract tests for data endpoints in `/Users/eliassoares/Documents/projects/personal/malipod/tests/contract/test_directory_api.py` (200/404 cases)

### Implementation

- [x] T019 [US4] Implement podcast metadata lookup in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/directory.py` (catalog-only; subscribers aggregation; build `mygpo_link` from server base URL)
- [x] T020 [US4] Implement episode metadata lookup in `/Users/eliassoares/Documents/projects/personal/malipod/app/services/directory.py` (by feed + media URL; 404 if not found; build `mygpo_link`)
- [x] T021 [US4] Implement data endpoints in `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/directory_api.py` (validate required query params; return 404 appropriately)

**Checkpoint**: US4 passes contract tests; mygpo_link uses server base URL; endpoints are public.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T022 [P] Update `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/quickstart.md` if manual verification steps need adjustment
- [x] T023 Run full verification (`make check` and `make test`) and fix any Ruff/MyPy/Bandit findings without `# noqa` / `# nosec` in `/Users/eliassoares/Documents/projects/personal/malipod/`
- [x] T024 Prepare PR summary update in `/Users/eliassoares/Documents/projects/personal/malipod/PR_SUMMARY.md` (scope + verification evidence)

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → (US1) → (US2) → (US3) → (US4) → Polish
- US2 depends on shared foundational service/router.
- US3 may require a small storage adjustment for categories/tags (T015) before queries are meaningful.

## Parallel Opportunities

- [P] tasks can run in parallel when they touch different files:
  - T004 (schemas) in parallel with T003 (validation helper)
  - T008/T011/T014/T018 (tests) can be prepared in parallel once endpoint shapes are fixed
  - Most contract test additions can be parallelized if they touch different sections/files
