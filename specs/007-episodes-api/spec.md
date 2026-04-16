# Feature Specification: Episodes API

**Feature Branch**: `007-episodes-api`
**Created**: 2026-04-16
**Status**: Draft
**Input**: User description: "Vamos desenvolver a api de episodes. The episode actions API is used to synchronize episode-related events between individual devices. Clients can send and store events on the webservice which makes it available to other clients. The following types of actions are currently accepted by the API: download, play, delete, new. Additional types can be requested on the Mailing List. Example use cases: Clients can send download and delete events so that other clients know where a file has already been downloaded. Clients can send play events with position information so that other clients know where to start playback. Clients can send new states to reset previous events. This state needs to be interpreted by receiving clients and does not delete any information on the webservice. Episode Action Types: download, delete, play, new, flattr. Upload Episode Actions: POST /api/2/episodes/(username).json. Get Episode Actions: GET /api/2/episodes/(username).json."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Episode Actions (Priority: P1)

As an authenticated podcast client, I want to upload episode-related actions for
my account so other clients can learn what happened to an episode and continue
playback or reuse downloaded files correctly.

**Why this priority**: Without upload support, no shared episode-state history
exists for other clients to consume, so synchronization cannot start.

**Independent Test**: An authenticated client can upload one or more valid
episode actions and receive a new server timestamp plus any rewritten URLs,
while invalid actions or cross-account requests are rejected.

**Acceptance Scenarios**:

1. **Given** an authenticated client uploads valid `download`, `delete`, `new`,
   `play`, or `flattr` actions for one account, **When** the request is
   processed, **Then** the service stores those actions for that user and
   returns a server-issued timestamp.
2. **Given** an authenticated client uploads a `play` action with valid
   playback progress fields, **When** the request is processed, **Then** the
   service stores that action so later clients can resume playback from the
   reported position.
3. **Given** an authenticated client uploads actions containing unsupported or
   rewritten podcast or episode URLs, **When** the request is processed,
   **Then** the service ignores the invalid semantic action and returns the
   rewrite pairs in `update_urls`.
4. **Given** an authenticated client targets a username other than its own
   account, **When** the upload is processed, **Then** the service rejects the
   request and does not store any action.

---

### User Story 2 - Retrieve Episode Actions (Priority: P1)

As an authenticated podcast client, I want to retrieve episode actions for my
account so I can synchronize playback, download, deletion, and reset events
that happened on other devices.

**Why this priority**: Reading actions is the client-visible payoff of the sync
surface and is required for cross-device continuity even when no advanced
filtering is used.

**Independent Test**: An authenticated client can request all actions or only
actions since a prior server timestamp and receive the matching action list plus
the next timestamp to store locally.

**Acceptance Scenarios**:

1. **Given** an authenticated client requests episode actions without a `since`
   value, **When** the request is processed, **Then** the service returns all
   episode actions stored for that user plus a fresh timestamp.
2. **Given** an authenticated client requests episode actions with a prior
   `since` value, **When** newer uploads exist, **Then** the service returns
   only actions uploaded after that timestamp plus a fresh timestamp.
3. **Given** an authenticated client requests episode actions with a prior
   `since` value and nothing newer exists, **When** the request is processed,
   **Then** the service returns an empty action list plus a fresh timestamp.
4. **Given** an authenticated client targets another user's username,
   **When** the request is processed, **Then** the service rejects the request
   instead of exposing another user's action history.

---

### User Story 3 - Filter and Aggregate Episode Actions (Priority: P2)

As an authenticated podcast client, I want to filter and aggregate retrieved
episode actions so I can synchronize just one podcast, one device, or the
latest action per episode when a full burst download would be too noisy.

**Why this priority**: Filtering and aggregation are valuable optimization
tools after the core upload and retrieval flows already work.

**Independent Test**: An authenticated client can request actions filtered by
podcast or device and can enable aggregation to receive only the latest action
for each episode in the matching result set.

**Acceptance Scenarios**:

1. **Given** an authenticated client requests actions for one podcast feed,
   **When** the request is processed, **Then** the service returns only actions
   for episodes belonging to that podcast.
2. **Given** an authenticated client requests actions for one device,
   **When** the request is processed, **Then** the service returns only actions
   that were logged for that device.
3. **Given** an authenticated client enables `aggregated=true`,
   **When** multiple actions exist for the same episode in the matching result
   set, **Then** the service returns only the latest action for that episode.
4. **Given** an authenticated client combines `since` with podcast or device
   filters, **When** the request is processed, **Then** the service applies all
   filters consistently and still returns a fresh timestamp.

### Edge Cases

- What happens when a `play` action includes only one or two of `started`,
  `position`, and `total` instead of the full set?
- How does the service behave when a request contains duplicate actions for the
  same episode in one upload batch?
- What happens when podcast or episode URLs contain non-ASCII characters,
  leading or trailing whitespace, or unsupported schemes?
- How does the service respond when `since` is negative, malformed, or greater
  than any known server-issued timestamp?
- What happens when a device filter references a device ID that has never been
  registered?
- How should `new` actions be interpreted when older episode actions still
  exist in the account history?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an authenticated contract compatible with
  `POST /api/2/episodes/{username}.json` for uploading episode actions for one
  user account.
- **FR-002**: The upload contract MUST accept batches of action objects
  containing `podcast`, `episode`, `action`, and optional `device`,
  `timestamp`, `started`, `position`, and `total` fields.
- **FR-003**: The system MUST identify podcasts by feed URL and episodes by
  media URL.
- **FR-004**: The upload contract MUST accept the action types `download`,
  `delete`, `play`, `new`, and `flattr`.
- **FR-005**: A `play` action MUST require `started`, `position`, and `total`
  together, and non-`play` actions MUST ignore playback progress fields.
- **FR-006**: The upload contract MUST store actions on a per-user basis rather
  than a per-device basis, while still allowing an optional device ID to be
  recorded for filtering and audit use.
- **FR-007**: The upload contract MUST return a JSON dictionary containing a
  server-issued `timestamp` and an `update_urls` list of rewritten URL pairs.
- **FR-008**: The system MUST sanitize uploaded podcast and episode URLs,
  rewriting URLs that contain non-ASCII characters or do not start with `http`
  or `https` to the empty string and ignoring those semantic actions.
- **FR-009**: The upload contract MUST reject requests that target a username
  other than the authenticated user's account.
- **FR-010**: The system MUST provide an authenticated contract compatible with
  `GET /api/2/episodes/{username}.json` for retrieving episode actions for one
  user account.
- **FR-011**: The retrieval contract MUST return a JSON object containing an
  `actions` list and a fresh server-issued `timestamp`.
- **FR-012**: When `since` is provided, the retrieval contract MUST return only
  actions uploaded after that server-issued timestamp, regardless of each
  action's own event timestamp.
- **FR-013**: When `since` is omitted, the retrieval contract MUST return all
  stored actions for the user.
- **FR-014**: The retrieval contract MUST support optional `podcast`, `device`,
  `since`, and `aggregated` query parameters.
- **FR-015**: When `podcast` is provided, the retrieval contract MUST return
  only actions for episodes associated with that podcast URL.
- **FR-016**: When `device` is provided, the retrieval contract MUST return
  only actions logged with that device ID.
- **FR-017**: When `aggregated=true`, the retrieval contract MUST return only
  the latest matching action for each episode.
- **FR-018**: When no matching actions exist, the retrieval contract MUST still
  return an empty `actions` list plus a fresh timestamp.
- **FR-019**: The retrieval contract MUST reject requests that target a
  username other than the authenticated user's account.
- **FR-020**: The service MUST preserve predictable ordering in responses so
  compatible clients can reconcile action history deterministically.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence for this feature MUST include automated
  coverage for valid upload batches, `play`-field validation, URL sanitation,
  cross-account denial, `since` filtering, podcast/device filtering,
  aggregation, and empty retrieval responses, plus manual validation of the two
  episode API contracts.
- **NFR-002**: Episode action endpoints MUST avoid leaking another user's
  playback, download, deletion, or device history through cross-account
  requests.
- **NFR-003**: Returned timestamps and action ordering MUST remain stable enough
  for clients to perform repeated incremental synchronization without ambiguity.
- **NFR-004**: The feature MUST extend the existing synchronization surface with
  the simplest persistence and filtering approach that satisfies the contracts
  without adding unnecessary user-facing scope.

### Key Entities *(include if feature involves data)*

- **Episode Action**: A user-scoped event describing what happened to one
  episode, including the podcast URL, episode media URL, action type, optional
  device ID, and optional playback-progress details.
- **Episode Action Batch**: A client-submitted list of episode actions uploaded
  together and acknowledged with one server-issued timestamp.
- **Episode Action Query**: A retrieval request that may limit the result set by
  timestamp, podcast URL, device ID, or aggregation mode.
- **URL Rewrite Result**: The original and sanitized URL pair returned when the
  service rewrites podcast or episode URLs during upload.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of validated episode-action uploads containing supported
  action types return a server-issued timestamp and preserve the uploaded
  account context.
- **SC-002**: 100% of validated `play` uploads that omit one of the required
  playback fields are rejected, while complete `play` uploads are accepted.
- **SC-003**: 100% of sanitized invalid podcast or episode URLs are reported in
  `update_urls` and do not create actionable episode-state records.
- **SC-004**: A client that stores the returned timestamp and performs a later
  retrieval receives only newer actions in at least 95% of validation
  scenarios.
- **SC-005**: 100% of validated retrievals using podcast, device, or
  aggregation filters return only actions matching the requested filter set.

## Assumptions

- Authentication already exists and reliably identifies the user account
  allowed to act on the targeted username.
- Device IDs used in episode actions follow the existing device-ID rules, but a
  device does not need to be explicitly registered before an action can mention
  it for logging and filtering purposes.
- The service may preserve uploaded event timestamps when provided, but
  incremental retrieval is based on server-issued sync timestamps rather than
  event occurrence time.
- The `new` action resets prior episode state from the perspective of receiving
  clients, but it does not delete older historical records from the service.
- The API stores and returns `flattr` actions when uploaded, even though the
  primary examples focus on `download`, `delete`, `play`, and `new`.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: Uploading actions, retrieving actions, and applying
  retrieval filters remain independently valuable and testable slices.
- **Branch Plan**: This feature is being specified on branch
  `007-episodes-api`, created from `main` in line with the constitution.
- **Verification Plan**: Before merge, the team must validate supported action
  uploads, `play` validation, URL rewrite reporting, `since` filtering,
  account-ownership checks, podcast/device filtering, aggregation behavior, and
  empty retrieval responses.
- **Quality Gate Strategy**: The implementation must satisfy lint, typing, and
  security checks by fixing root causes directly rather than suppressing
  findings with inline waivers.
- **Review Readiness**: The final pull request must summarize the delivered
  upload/retrieval contracts, filters supported, validation behaviors tested,
  and any follow-up sync scope intentionally deferred.
- **Security/Simplicity Notes**: Planning must justify how user-scoped episode
  history, device filtering, URL sanitation, and incremental timestamps remain
  secure and minimal without introducing unnecessary complexity.
