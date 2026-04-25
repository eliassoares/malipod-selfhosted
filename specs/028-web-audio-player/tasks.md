# Tasks: Web Audio Player Bar

**Input**: Design documents from `/Users/eliassoares/Documents/projects/personal/malipod/specs/028-web-audio-player/`
**Prerequisites**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/028-web-audio-player/plan.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/028-web-audio-player/spec.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/028-web-audio-player/research.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/028-web-audio-player/data-model.md`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/028-web-audio-player/contracts/`, `/Users/eliassoares/Documents/projects/personal/malipod/specs/028-web-audio-player/quickstart.md`

**Tests**: Add unit coverage for web player state persistence and device idempotency; add contract/integration coverage for `/web/*` endpoints and template injection; add integration coverage for “player bar present on authenticated pages”.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm integration points and current templates/services to extend.

- [x] T001 Confirm working branch is `028-web-audio-player` and feature directory is `specs/028-web-audio-player/`
- [x] T002 Review current `base.html` and partials layout for site-wide UI injection (`app/templates/base.html`, `app/templates/partials/*.html`)
- [x] T003 Review existing episode actions pipeline used by gpodder endpoints (`app/services/episodes.py`, `app/api/routes/episodes_api.py`)
- [x] T004 Review playlists detail page for queue initiation integration (`app/templates/playlists/detail.html`, `app/api/routes/episode_playlists_site.py`, `app/services/episode_playlists.py`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add persistence primitives + endpoints scaffolding needed by all user stories.

- [x] T005 Add Alembic migration for user last-player columns (`alembic/versions/0017_web_player_last_state.py`, `app/db/models/user.py`)
- [x] T006 Add Alembic migration for `episode_playlist_items.position` with backfill per playlist (`alembic/versions/0018_playlist_item_position.py`, `app/db/models/podcast.py`)
- [x] T007 Add/extend `UserModel` fields for last-player state (`app/db/models/user.py`, `app/db/models/__init__.py`)
- [x] T008 Add/extend `EpisodePlaylistItemModel` with `position` and update ordering/insert behavior (`app/db/models/podcast.py`, `app/services/episode_playlists.py`)
- [x] T009 Implement `WebPlayerService` for state upsert + get-or-create web device + action recording (`app/services/web_player.py`)
- [x] T010 Add JSON schemas for web player endpoints (`app/schemas/web_player.py`)
- [x] T011 Add new API router for `/web/*` endpoints (`app/api/routes/web_player_api.py`, `app/main.py`, `app/api/deps.py`)

**Checkpoint**: DB migrations exist; service can persist state and create web device idempotently; endpoints are wired and authenticated.

---

## Phase 3: User Story 1 - Reproduzir com barra persistente (Priority: P1) 🎯 MVP

**Goal**: Always-visible player bar with basic controls and persistence across page navigation within a browser session.

**Independent Test**: Start playback from an episode page, navigate to another page, and verify bar remains visible and restores state.

### Tests for User Story 1 ⚠️

- [x] T012 [P] [US1] Add integration tests asserting player bar partial is present on authenticated pages (`tests/integration/test_player_bar_presence.py`)
- [x] T013 [P] [US1] Add integration tests for template injection `window.__PLAYER_STATE__` null vs populated (`tests/integration/test_player_state_injection.py`)

### Implementation for User Story 1

- [x] T014 [US1] Add `partials/player_bar.html` and include it in `base.html` (sticky footer bar, empty state) (`app/templates/partials/player_bar.html`, `app/templates/base.html`)
- [x] T015 [US1] Inject `window.__PLAYER_STATE__` in `base.html` for authenticated users (`app/templates/base.html`, relevant site route context where needed)
- [x] T016 [US1] Add `player.js` with `MaliPlayer` scaffolding (load/pause/play/seek, UI binding, sessionStorage restore) (`app/static/js/player.js`)
- [x] T017 [US1] Add “Play” button integration on episode detail page calling `MaliPlayer.load(episodeId, position)` (`app/templates/episodes/detail.html`, optional: `app/api/routes/episode_site.py` for data attributes)

**Checkpoint**: US1 tests pass; player bar always visible; episode detail can initialize player; state survives navigation via sessionStorage restore.

---

## Phase 4: User Story 2 - Fila e avanço automático (Priority: P2)

**Goal**: Support playlist-mode queue and podcast-mode queue, with automatic advance on `ended`.

**Independent Test**: Start playback from a playlist and confirm automatic advancement; start playback from an episode and confirm next episode is selected.

### Tests for User Story 2 ⚠️

- [x] T018 [P] [US2] Add integration test for playlist “Play Playlist” wiring and queue payload presence (`tests/integration/test_playlist_play_button.py`)
- [x] T019 [P] [US2] Add contract tests for `GET /web/episode/{id}/next` selecting the correct next episode (`tests/contract/test_web_player_next_episode.py`)

### Implementation for User Story 2

- [x] T020 [US2] Add “Play Playlist” button in playlist detail template, exposing ordered episode ids (`app/templates/playlists/detail.html`)
- [x] T021 [US2] Implement playlist queue order by `EpisodePlaylistItemModel.position` and expose via page context (`app/api/routes/episode_playlists_site.py`, `app/services/episode_playlists.py`)
- [x] T022 [US2] Implement `GET /web/episode/{id}/next` endpoint (podcast mode) (`app/api/routes/web_player_api.py`, `app/services/web_player.py`)
- [x] T023 [US2] Implement `MaliPlayer.setQueue()` + `next()` + `ended` handler for auto-advance (`app/static/js/player.js`)

**Checkpoint**: Playlist queue advances; podcast-mode queue advances via `/web/episode/{id}/next`.

---

## Phase 5: User Story 3 - Retomar e registrar histórico (Priority: P3)

**Goal**: Persist last state server-side and register play/pause/completion events using a dedicated web device.

**Independent Test**: Listen, persist state, reload page; verify injected state restores and that action events are written.

### Tests for User Story 3 ⚠️

- [x] T024 [P] [US3] Add unit tests for `WebPlayerService.get_or_create_web_device()` idempotency (`tests/unit/test_web_player_service.py`)
- [x] T025 [P] [US3] Add unit tests for `WebPlayerService.upsert_state()` persisting last state (`tests/unit/test_web_player_service.py`)
- [x] T026 [P] [US3] Add contract tests for `POST /web/player/action` and `POST /web/player/state` (`tests/contract/test_web_player_api.py`)

### Implementation for User Story 3

- [x] T027 [US3] Implement `POST /web/player/state` endpoint updating user last state (`app/api/routes/web_player_api.py`, `app/services/web_player.py`)
- [x] T028 [US3] Implement `POST /web/player/action` endpoint: ensure web device exists and record episode action event via `EpisodeService.upload_actions` (`app/api/routes/web_player_api.py`, `app/services/web_player.py`, `app/services/episodes.py`)
- [x] T029 [US3] Implement JS persistence throttle: every ~10s during play and on pause/stop; call endpoints with JSON payload (`app/static/js/player.js`)
- [x] T030 [US3] Ensure any authenticated page receives player state injection (null or payload) consistently (`app/templates/base.html`, site route contexts as needed)

**Checkpoint**: US3 tests pass; last episode/progress persists and re-injects; action events created with `device_id="web-player"`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, documentation, and PR readiness.

- [x] T031 Run full quality gates: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy app/ tests/`, `uv run bandit -r app -c pyproject.toml`, `uv run pip-audit`
- [x] T032 Validate manual steps in `/Users/eliassoares/Documents/projects/personal/malipod/specs/028-web-audio-player/quickstart.md`
- [x] T033 Prepare PR summary (scope, verification evidence, screenshots optional, follow-ups) in `PR_SUMMARY.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → required to locate current injection points and existing services.
- **Foundational (Phase 2)** → blocks UI work and endpoint work (migrations + service + schemas + router wiring).
- **US1 (Phase 3)** → delivers MVP (bar + basic controls + persistence via sessionStorage + injection).
- **US2 (Phase 4)** → adds queues and auto-advance.
- **US3 (Phase 5)** → adds server-side persistence and historical events.
- **Polish (Phase 6)** → after stories complete.

### Parallel Opportunities

- [P] tests that touch different files can proceed in parallel once Phase 2 endpoints/services are in place.
- [P] template + JS work can proceed after the bar partial is defined and included.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (migrations/service/router scaffolding)
2. Phase 3 (US1): bar + JS scaffolding + episode play wiring
3. Verify navigation persistence and player bar presence

### Incremental Delivery

1. US1 → US2 → US3
2. Run Phase 6 quality gates and prepare PR summary
