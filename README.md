# Malipod

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/eliassoares/malipod-selfhosted/actions/workflows/ci.yml/badge.svg)](https://github.com/eliassoares/malipod-selfhosted/actions/workflows/ci.yml)

Malipod is a self-hosted [gpodder.net](https://gpoddernet.readthedocs.io/en/latest/api/index.html)-compatible
podcast synchronization server. It implements the full gpodder.net v2 API, enabling
podcast apps like AntennaPod to sync subscriptions, episode actions, and device
state across multiple clients.

## Features

### Podcast app sync (gpodder.net v2 API)

Malipod is a drop-in replacement for gpodder.net. Any app that supports the
gpodder.net v2 API — including AntennaPod — can point to your Malipod instance
and sync subscriptions, episode progress, and device state across all your
devices without sending any data to third-party servers.

### Add podcasts by URL

On the Subscriptions page, paste any RSS/Atom feed URL into the "Add podcast"
field and click **Add**. Malipod fetches and imports the feed metadata in the
background, then adds the podcast to your library. The episode list, artwork,
author, and description are all stored locally.

### Episode playlists

Create and manage custom playlists of episodes from the **Playlists** page
(`/user/{nickname}/playlists`):

- **Create** a playlist with a title, optional description, and cover image
  (PNG, JPEG, or WebP, up to 1 MB).
- **Edit** the title, description, or cover image at any time.
- **Delete** a playlist with a confirmation step.
- **Detail page** — search your subscribed episodes by title or podcast name to
  add or remove them. Each episode row links directly to its episode page.
- **Favorites playlist** — a built-in read-only playlist populated automatically
  from your favorited episodes. Open it to browse and selectively unfavorite
  episodes without leaving the playlists area.

Each playlist card shows the episode count and total listening time. Playlists
and their items are included in the export/import snapshot, so they survive
account migrations.

### Favorites

Both podcasts and individual episodes can be favorited from their detail pages.
Favorited podcasts are accessible through the **Favorites** filter on the
Subscriptions page. The gpodder.net Favorites API
(`GET /api/2/favorites/{username}.json`) also exposes favorited episodes to
compatible clients.

### Listening metrics

The **Metrics** page (`/user/{nickname}/stats`) shows:

- **Highlights** — total content completed, completed episodes, and followed podcasts
- **Top by time** — the 5 podcasts you've spent the most time on
- **Top by completed** — the 5 podcasts with the most completed episodes

Each **podcast detail page** shows per-podcast listening stats: completion rate,
episodes in progress, and the date of the last episode played.

Each **episode detail page** shows per-episode stats: progress percentage and
bar, play count, first and last play date, and the date it was favorited (if
applicable).

### Centralized subscription sync

By default, subscriptions are synced per device (standard gpodder.net
behaviour). Enable **Centralized sync** in Settings to merge all your devices
into one unified list:

- **Off** — each device syncs its own subscription list independently.
- **On** — all devices share one unified list. Subscribing on any device makes
  the podcast available everywhere; a podcast only leaves the list once it is
  removed from every device. Fully transparent to the podcast app — no client
  changes required.

### Export and import data

From the Settings page, you can:

- **Export** — download a full JSON snapshot of your account: subscriptions,
  episode actions, favorites, and settings.
- **Import** — restore from a previously exported snapshot, merging the data
  into your current account.

This makes it easy to migrate between Malipod instances or keep an offline
backup of your listening history.

### Privacy and data control

Malipod is self-hosted — your listening history never leaves your server.
The Settings page provides two irreversible deletion options:

- **Delete data** — removes all episode actions, subscriptions, favorites, and
  settings while keeping the account active.
- **Delete account** — permanently removes the account and all associated data.

Both actions require confirmation and are scoped strictly to the authenticated
user's own data.

### Multi-language web UI

The web interface is available in **English**, **Spanish**, and
**Brazilian Portuguese**. The language can be switched at any time from the
top navigation bar; the choice is persisted in a cookie and remembered across
sessions.

---

## Stack

- Python 3.13
- FastAPI + Uvicorn
- SQLAlchemy 2.x + asyncpg
- PostgreSQL for development/runtime
- SQLite for automated tests
- Docker Compose for local execution

## Configuration

Copy the example environment file and replace the secret before running the app:

```bash
cp .env.example .env
```

Required settings:

- `APP_NAME`
- `ENVIRONMENT`
- `LOG_LEVEL`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `TEST_DATABASE_URL`
- `SECRET_KEY`

Generate a secure `SECRET_KEY` with:

```bash
openssl rand -hex 32
```

The application validates configuration at startup and fails safely if required
values are missing or insecure.

## Run Locally

### Development (Docker)

Starts the app with hot-reload and a managed PostgreSQL container. Dev
dependencies (pytest, ruff, mypy, etc.) are included in the image.

```bash
cp .env.example .env   # adjust values if needed
make dev-up
make dev-logs          # optional: tail logs
make dev-down          # stop
```

### Production (Docker)

Connects to an existing PostgreSQL instance — no database container is started.
Only runtime dependencies are installed in the image.

```bash
cp .env.prod.example .env.prod   # fill in DATABASE_URL and SECRET_KEY
make prod-up
make prod-logs                   # optional: tail logs
make prod-down                   # stop
```

### Local process (no Docker)

```bash
uv sync
cp .env.example .env
make run
```

## gpodder.net API Compatibility

Malipod implements the [gpodder.net v2 API](https://gpoddernet.readthedocs.io/en/latest/api/index.html).
All endpoints send `Access-Control-Allow-Origin: *` for CORS compatibility.

### Authentication API (v2.10)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/2/auth/{username}/login.json` | Basic | Login, returns session cookie |
| POST | `/api/2/auth/{username}/logout.json` | Session | Logout, invalidates session |

### Device API (v2.0+)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/2/devices/{username}.json` | Basic | List all devices |
| POST | `/api/2/devices/{username}/{deviceid}.json` | Basic | Create or update device |
| GET | `/api/2/updates/{username}/{deviceid}.json` | Basic | Get device updates since timestamp |

Query params for updates: `since` (int), `include_actions` (bool).

### Subscriptions API (v1.0+)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/subscriptions/{username}.{format}` | Basic | All subscriptions (v2.11) |
| GET | `/subscriptions/{username}/{deviceid}.{format}` | Basic | Device subscriptions |
| PUT | `/subscriptions/{username}/{deviceid}.{format}` | Basic | Replace device subscriptions |
| POST | `/api/2/subscriptions/{username}/{deviceid}.json` | Basic | Upload subscription changes (delta) |
| GET | `/api/2/subscriptions/{username}/{deviceid}.json` | Basic | Get subscription changes (delta) |

Formats: `json`, `opml`, `txt`. JSONP supported via `?jsonp=callback` on GET endpoints.

### Episode Actions API (v2.0+)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/2/episodes/{username}.json` | Basic | Upload episode actions |
| GET | `/api/2/episodes/{username}.json` | Basic | Get episode actions |

Query params for GET: `podcast`, `device`, `since`, `aggregated`.
Actions: `play`, `new`, `download`, `delete`, `flattr`.

### Directory API (v1.0+)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/search.{format}` | None | Search podcasts |
| GET | `/toplist/{number}.{format}` | None | Top podcasts by subscribers |
| GET | `/api/2/tags/{count}.json` | None | Top tags |
| GET | `/api/2/tag/{tag}/{count}.json` | None | Podcasts by tag |
| GET | `/api/2/data/podcast.json` | None | Podcast metadata |
| GET | `/api/2/data/episode.json` | None | Episode metadata |

Query params for search/toplist: `jsonp`, `scale_logo`.
Formats: `json`, `opml`, `txt`.

### Suggestions API (v1.0+)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/suggestions/{number}.{format}` | Basic | Podcast suggestions |

Returns podcasts the user hasn't subscribed to, ranked by popularity among other users.
Query params: `jsonp`. Formats: `json`, `opml`, `txt`.

### Settings API (v2.4)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/2/settings/{username}/{scope}.json` | Basic | Get settings |
| POST | `/api/2/settings/{username}/{scope}.json` | Basic | Update settings |

Scopes: `account`, `device`, `podcast`, `episode`.
Context query params: `device`, `podcast`, `episode` (as required by scope).

### Favorites API (v2.6)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/2/favorites/{username}.json` | Basic | Get favorite episodes |

### Podcast Lists API (v2.10)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/2/lists/{username}.json` | None | List user's podcast lists |
| GET | `/api/2/lists/{username}/list/{name}.{format}` | None | Get podcast list |
| POST | `/api/2/lists/{username}/create.{format}` | Basic | Create podcast list |
| PUT | `/api/2/lists/{username}/list/{name}.{format}` | Basic | Update podcast list |
| DELETE | `/api/2/lists/{username}/list/{name}.{format}` | Basic | Delete podcast list |

Formats: `json`, `opml`, `txt`.

### Device Synchronization API (v2.10)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/2/sync-devices/{username}.json` | Basic | Get sync group status |
| POST | `/api/2/sync-devices/{username}.json` | Basic | Start/stop device sync |

### Client Parametrization

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/clientconfig.json` | None | Client configuration (base URLs, timeout) |

### Additional Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health/live` | Liveness probe |
| GET | `/api/v1/health/ready` | Readiness probe |
| GET | `/` | Web UI home |
| GET/POST | `/register` | User registration |
| GET/POST | `/login` | Web login |
| POST | `/logout` | Web logout |
| GET | `/user/profile/{nickname}` | User profile |

### Supported Formats

| Format | Description |
|--------|-------------|
| `json` | JSON (primary format for all endpoints) |
| `opml` | OPML (subscriptions, lists, directory, suggestions) |
| `txt` | Plain text, one URL per line |
| `jsonp` | Via `?jsonp=callback` query param on GET JSON endpoints |

### Known Limitations vs gpodder.net

| Feature | Status | Notes |
|---------|--------|-------|
| XML format (v2.9+) | Not supported | OPML covers subscription export use case |
| `scaled_logo_url` | Always null | No logo scaling service |
| `position_last_week` | Always 0 | No historical ranking data |
| `subscribers_last_week` | Always 0 | No historical subscriber tracking |
| `scale_logo` param | Accepted, ignored | No scaling CDN |

### AntennaPod Compatibility

All 7 endpoints required by AntennaPod are fully implemented:
login, list devices, configure device, upload/get subscription changes,
upload/get episode actions. See `specs/antennapod-compat.md` for details.

## Verification

Run the full local verification workflow:

```bash
make verify
```

This executes:

- `uv run ruff check .`
- `uv run mypy .`
- `uv run bandit -r . -c pyproject.toml`
- `uv run pip-audit`
- `uv run pytest`

Feature-specific shortcuts:

- `make verify-auth`
- `make verify-device`
- `make verify-subscriptions`
- `make verify-episodes`
- `make verify-lists`

## Contribution Workflow

- Create a feature branch from `main`
- Use Conventional Commits, for example `feat(api): add readiness endpoint`
- Run `make verify` before review
- Open a pull request with scope, verification evidence, and follow-up items
