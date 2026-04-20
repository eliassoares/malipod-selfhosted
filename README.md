# Malipod

Malipod is a self-hosted [gpodder.net](https://gpoddernet.readthedocs.io/en/latest/api/index.html)-compatible
podcast synchronization server. It implements the full gpodder.net v2 API, enabling
podcast apps like AntennaPod to sync subscriptions, episode actions, and device
state across multiple clients.

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

The application validates configuration at startup and fails safely if required
values are missing or insecure.

## Run Locally

### Docker Compose

```bash
docker compose up --build
```

### Local process

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
