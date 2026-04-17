# Feature Specification: Settings API

**Feature Branch**: `009-settings-api`
**Created**: 2026-04-17
**Status**: Draft
**Input**: User description: "Vamos desenvolver a api de settings. Clients can store settings and retrieve settings as key-value-pairs, which are attached to either account, device, podcast or episode. Known Settings: Account public_profile, store_user_agent, public_subscriptions; Episode is_favorite; Podcast public_subscription. Save Settings: POST /api/2/settings/(username)/(scope).json. Get Settings: GET /api/2/settings/(username)/(scope).json."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Scoped Settings (Priority: P1)

As an authenticated client, I want to retrieve the settings stored for one
scope of a user account so I can synchronize account, device, podcast, or
episode preferences correctly.

**Why this priority**: Reading current settings is the foundation for client
sync behavior and is immediately useful even before clients start changing any
values.

**Independent Test**: A client can request settings for each supported scope
with the required identifying query parameters and receive only the current
key-value pairs for that scope, while invalid scope references are rejected.

**Acceptance Scenarios**:

1. **Given** an authenticated user has account-level settings, **When** a
   client requests `GET /api/2/settings/{username}/account.json`, **Then** the
   service returns the user's current account settings as a JSON object.
2. **Given** an authenticated user has device-level settings for a known
   device, **When** a client requests that device scope with the required
   device identifier, **Then** the service returns only the settings attached
   to that device.
3. **Given** an authenticated user has podcast-level or episode-level settings,
   **When** a client supplies the required podcast and episode identifiers for
   the requested scope, **Then** the service returns only the settings for that
   exact scope target.
4. **Given** a client omits a required identifying query parameter for the
   selected scope, **When** the request is processed, **Then** the service
   rejects the request and does not return a partial settings payload.

---

### User Story 2 - Save and Remove Scoped Settings (Priority: P1)

As an authenticated client, I want to add, update, and remove settings within a
scope in one request so I can keep synchronized preference state without making
multiple round trips.

**Why this priority**: The core value of the feature is reliable settings
storage and synchronization across clients, which depends on the write
contract.

**Independent Test**: A client can submit a valid `set` map and `remove` list
for a supported scope and receive the full resulting settings object after the
update, while cross-account or malformed requests are rejected.

**Acceptance Scenarios**:

1. **Given** an authenticated user targets one of their own supported scopes,
   **When** the client submits a valid save request with new settings, **Then**
   the service stores those values and returns the full settings object after
   the update.
2. **Given** an authenticated user submits a save request that removes one or
   more existing keys, **When** the update is applied, **Then** the response no
   longer includes those removed keys.
3. **Given** an authenticated user submits both additions and removals in the
   same request, **When** the update is processed, **Then** the final response
   reflects the complete resulting state for that scope.
4. **Given** an authenticated user targets another username, **When** the save
   request is processed, **Then** the service rejects the request and does not
   change the targeted settings.

---

### User Story 3 - Preserve Scope Rules and Known Settings Semantics (Priority: P2)

As a product maintainer, I want the settings API to enforce scope-specific
identifiers and preserve recognized setting names so clients and website
behavior remain consistent.

**Why this priority**: Scope validation and known setting compatibility protect
data integrity, but the feature still has clear value if basic read and write
flows ship first.

**Independent Test**: A client can round-trip recognized settings on the
documented scopes, store arbitrary JSON values, and receive consistent
validation when scope identifiers are missing or incompatible.

**Acceptance Scenarios**:

1. **Given** a client stores recognized account, podcast, or episode settings,
   **When** the settings are later retrieved, **Then** the keys and JSON values
   remain intact for the same scope.
2. **Given** a client stores a nested JSON object, array, boolean, number, or
   null as a setting value, **When** the settings are retrieved, **Then** the
   value matches the stored JSON structure.
3. **Given** a client requests episode scope without both the podcast and
   episode identifiers, **When** the request is processed, **Then** the service
   rejects the request because the scope target is incomplete.
4. **Given** a client references a scope target that does not exist for the
   user, **When** the request is processed, **Then** the service returns the
   documented not-found behavior for that missing target.

### Edge Cases

- How does the service respond when `scope` is not one of `account`, `device`,
  `podcast`, or `episode`?
- What happens when a request includes malformed JSON, a non-object `set`
  payload, or a non-array `remove` payload?
- How should the service behave when the same key appears in both `set` and
  `remove` within one save request?
- What is returned when a client removes keys that do not currently exist in
  the targeted scope?
- How are requests handled when the targeted device, podcast, or episode
  reference does not exist for the user?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide `GET /api/2/settings/{username}/{scope}.json`
  for reading settings and `POST /api/2/settings/{username}/{scope}.json` for
  saving settings.
- **FR-002**: The system MUST require authentication for both read and save
  operations on settings.
- **FR-003**: The system MUST support exactly four scopes for this feature:
  `account`, `device`, `podcast`, and `episode`.
- **FR-004**: The system MUST reject requests that target a username other than
  the authenticated account for write operations.
- **FR-005**: The system MUST reject requests that do not satisfy the required
  identifying query parameters for the selected scope.
- **FR-006**: The account scope MUST require no additional identifying query
  parameters beyond the targeted username.
- **FR-007**: The device scope MUST require a device identifier query
  parameter.
- **FR-008**: The podcast scope MUST require a podcast feed URL query
  parameter.
- **FR-009**: The episode scope MUST require both a podcast feed URL query
  parameter and an episode media URL query parameter.
- **FR-010**: The save request body MUST accept a `set` object containing keys
  to add or update and a `remove` array containing keys to delete.
- **FR-011**: The system MUST treat setting keys as strings and MUST preserve
  setting values as valid JSON values.
- **FR-012**: After a successful save request, the response MUST return the
  complete resulting settings object for the targeted scope.
- **FR-013**: A successful read request MUST return the complete current
  settings object for the targeted scope.
- **FR-014**: The system MUST store settings independently per scope target so
  account, device, podcast, and episode settings do not overwrite one another.
- **FR-015**: Removing a key that exists in the targeted scope MUST delete that
  key from the resulting settings object.
- **FR-016**: Removing a key that does not exist in the targeted scope MUST NOT
  create a new key and MUST leave other settings unchanged.
- **FR-017**: The system MUST support the documented known setting names for
  account (`public_profile`, `store_user_agent`, `public_subscriptions`),
  podcast (`public_subscription`), and episode (`is_favorite`) scopes.
- **FR-018**: The system MUST allow clients to store and retrieve additional
  unrecognized setting keys beyond the known settings list.
- **FR-019**: The system MUST return a not-found response when the targeted
  username or scope target does not exist.
- **FR-020**: The system MUST reject unsupported scope values instead of
  treating them as another valid scope.
- **FR-021**: The system MUST apply save requests atomically for one targeted
  scope so clients receive a consistent final settings object.
- **FR-022**: The system MUST preserve the exact scope target identity used for
  storage so settings remain attached to the intended account, device, podcast,
  or episode.
- **FR-023**: The system MUST support round-tripping arbitrary valid JSON
  values, including objects, arrays, booleans, numbers, strings, and null.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence for this feature MUST include automated
  coverage for authenticated reads, authenticated saves, scope-specific query
  validation, arbitrary JSON round-tripping, key removal, malformed payload
  rejection, not-found behavior, and cross-account write denial.
- **NFR-002**: Settings operations MUST protect user privacy by preventing one
  authenticated account from modifying another account's settings through this
  API.
- **NFR-003**: The feature MUST extend the existing API contracts with the
  simplest storage and retrieval behavior that satisfies the documented scopes
  and setting semantics without introducing unrelated preference-management
  features.

### Key Entities *(include if feature involves data)*

- **Scoped Setting Collection**: A set of key-value pairs attached to exactly
  one scope target belonging to one user account.
- **Scope Target**: The identifier set that determines where settings belong:
  account, one device, one podcast subscription, or one episode within a
  podcast.
- **Setting Mutation Request**: The requested combination of keys to add or
  update and keys to remove for one scope target.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of validated authenticated `GET` requests for an existing
  scope target return only the current settings for that exact target.
- **SC-002**: 100% of validated authenticated `POST` requests return the full
  resulting settings object reflecting all accepted additions, updates, and
  removals for the targeted scope.
- **SC-003**: 100% of requests missing required scope-identifying query
  parameters are rejected without changing stored settings.
- **SC-004**: 100% of validated settings values using supported JSON types can
  be retrieved without loss of structure or type.
- **SC-005**: 100% of cross-account write attempts are rejected without
  modifying another user's settings.

## Assumptions

- Existing authentication already identifies the requesting user account and is
  available to protect these endpoints.
- Website-side behavior triggered by known settings is not newly expanded by
  this feature beyond preserving and exposing the documented setting keys
  through the API.
- Device, podcast, and episode references already have a canonical way to be
  identified for one user through the documented query parameters.
- The API returns settings objects in JSON even when no settings have yet been
  stored for a valid scope target.
- A malformed request body or invalid scope reference is rejected without
  partially applying any requested setting changes.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: Reading scoped settings, saving scoped settings, and
  enforcing scope-specific compatibility are independently valuable slices that
  can be implemented and demonstrated in priority order.
- **Branch Plan**: This feature is being specified on branch
  `009-settings-api`, created from `main` in line with the constitution.
- **Verification Plan**: Before merge, the team must validate authenticated
  reads, authenticated writes, scope parameter rules, arbitrary JSON storage,
  key removal behavior, malformed payload handling, not-found responses, and
  cross-account protections.
- **Quality Gate Strategy**: The implementation must satisfy lint, typing, and
  security checks by fixing the underlying issues directly instead of relying on
  inline suppressions.
- **Review Readiness**: The final pull request must summarize the supported
  scopes, query-parameter rules, known setting compatibility, response
  contracts, and any documented assumptions about missing scope targets.
- **Security/Simplicity Notes**: Planning must justify how scope ownership,
  target validation, and arbitrary JSON handling remain secure and minimal
  without adding unnecessary preference-management complexity.
