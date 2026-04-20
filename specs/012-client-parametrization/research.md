# Research: Client Parametrization

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/spec.md`

## Decisions

### 1) Endpoint location and routing

- **Decision**: Implement `GET /clientconfig.json` as a new public router module
  at `/Users/eliassoares/Documents/projects/personal/malipod/app/api/routes/client_config.py`
  and include it in `/Users/eliassoares/Documents/projects/personal/malipod/app/main.py`.
- **Rationale**: Keeps the endpoint isolated from site HTML routes and from the
  authenticated API surface (`/api/*`), while matching existing router patterns.
- **Alternatives considered**:
  - Add to `site.py`: rejected to avoid mixing HTML and JSON contracts in one router.
  - Add under `/api/v1`: rejected because the contract is a fixed root path (`/clientconfig.json`).

### 2) Response contract shape

- **Decision**: Return a JSON object with:
  - `mygpo.baseurl` (string)
  - `mygpo-feedservice.baseurl` (string; compatibility field, same value)
  - `update_timeout` (positive integer, seconds; default 86400)
- **Rationale**: Matches the feature spec requirements (FR-002/004/006) and keeps
  compatibility-oriented fields present even when feedservice is not implemented.
- **Alternatives considered**:
  - Omit `mygpo-feedservice`: rejected because spec recommends it for compatibility.
  - Make `update_timeout` configurable: rejected because spec explicitly disallows
    new settings (NFR-003).

### 3) Base URL normalization

- **Decision**: Always normalize the configured base URL to exactly one trailing
  slash in the response.
- **Rationale**: Prevents client URL concatenation bugs and satisfies the trailing
  slash acceptance scenario.
- **Alternatives considered**:
  - Return base URL unchanged: rejected due to edge-case requirement.
  - Always strip trailing slash: rejected because clients commonly append paths.

### 4) Content negotiation and content-type

- **Decision**: Always respond with JSON and `Content-Type: application/json`,
  regardless of `Accept` header presence.
- **Rationale**: Satisfies the edge case and aligns with FastAPI’s JSON defaults.
- **Alternatives considered**:
  - Require `Accept: application/json`: rejected; spec requires JSON even without it.

### 5) Verification strategy

- **Decision**: Add a contract test that validates:
  - `200 OK` without authentication
  - JSON contains required fields
  - `mygpo.baseurl` matches configured base URL and is normalized
  - `update_timeout` is a positive integer
- **Rationale**: Provides high-signal verification for an externally consumed
  contract and prevents regressions.
- **Alternatives considered**:
  - Only manual verification: rejected (NFR-001 requires automated tests).
