# Feature Specification: Device API

**Feature Branch**: `005-device-api`
**Created**: 2026-04-15
**Status**: Draft
**Input**: User description: "Vamos desenvolver a api de devices. Os devices são usados em toda a API para identificar um device/aplicativo cliente. Um ID de dispositivo pode ser qualquer string que corresponda à expressão regular [\\w.-]+. O aplicativo cliente deve gerar uma string para ser usada como seu ID de dispositivo e deve garantir que ela seja exclusiva dentro da conta do usuário. Uma boa prática é combinar o nome do aplicativo com o nome do host em que ele está sendo executado."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register and Update a Device Identity (Priority: P1)

As an authenticated API client, I want to create or update my device record for a
specific user so the service can recognize this client instance across future
sync operations.

**Why this priority**: Device identity is the foundation for all later
device-scoped synchronization behavior and must exist before clients can safely
exchange updates.

**Independent Test**: An authenticated client can submit a valid device ID for a
target user, set or change the human-readable caption and device type, and then
retrieve the same device details later through the list flow.

**Acceptance Scenarios**:

1. **Given** an authenticated user targets their own account and provides a
   valid new device ID, **When** they submit a caption and device type, **Then**
   the system stores a device record for that user and preserves the supplied
   identifier.
2. **Given** an authenticated user targets an existing device they already own,
   **When** they submit only one supported field such as caption or type,
   **Then** the system updates only the supplied fields and leaves other device
   data unchanged.
3. **Given** an authenticated client submits a device ID that does not match the
   allowed device identifier pattern, **When** the request is processed, **Then**
   the system rejects the request and explains that the identifier format is
   invalid.
4. **Given** an authenticated client targets a different username than the
   account represented by their authentication context, **When** they attempt to
   create or update a device, **Then** the system rejects the request.

---

### User Story 2 - List Devices for an Account (Priority: P1)

As an authenticated user, I want to list the devices associated with my account
so I can choose which client context to use for subscriptions and synchronization
flows.

**Why this priority**: Users and compatible clients need visibility into
registered devices before they can trust device-based subscription retrieval and
cross-client behavior.

**Independent Test**: An authenticated user with one or more devices can request
their device list and receive a complete account-scoped summary including each
device ID, human-readable caption, device type, and subscription count.

**Acceptance Scenarios**:

1. **Given** an authenticated user has multiple registered devices, **When**
   they request their device list, **Then** the system returns only the devices
   that belong to that user.
2. **Given** an authenticated user has a device without a caption, **When**
   they request their device list, **Then** the system includes that device with
   an empty caption rather than inventing a placeholder name.
3. **Given** an authenticated user has no registered devices, **When** they
   request their device list, **Then** the system returns an empty list rather
   than an error.

---

### User Story 3 - Retrieve Device-Specific Updates (Priority: P2)

As an authenticated API client, I want to fetch changes relevant to a specific
device since my last sync so I can keep subscriptions and episode states aligned
without reprocessing the entire account history.

**Why this priority**: Incremental device updates build on registered device
identity and make the synchronization model practical for ongoing client usage.

**Independent Test**: An authenticated client can request updates for a known
device, optionally filter by a previously returned timestamp, and receive a
response containing added subscriptions, removed subscriptions, episode updates,
and a fresh timestamp for the next sync.

**Acceptance Scenarios**:

1. **Given** an authenticated client requests updates for a known device without
   a prior timestamp, **When** the system processes the request, **Then** it
   returns the current add, remove, and episode update collections plus a new
   timestamp.
2. **Given** an authenticated client provides a prior timestamp, **When** the
   system processes the request, **Then** it returns only changes that occurred
   after that timestamp for the targeted account and device context.
3. **Given** an authenticated client requests updates with action details
   enabled, **When** an updated episode has a state other than new, **Then** the
   system includes the latest reported user action for that episode.
4. **Given** an authenticated client requests updates for a device ID that does
   not belong to the targeted user, **When** the request is processed, **Then**
   the system rejects the request instead of leaking another account's sync data.

## Edge Cases

- What happens when a client reuses a valid device ID that already exists under
  the same user but changes the caption or type repeatedly?
- What happens when a client submits a valid device ID for one user that is also
  used by another user account?
- How does the system respond when a client omits both updatable device fields in
  a device update request?
- What happens when the device type is outside the supported set of desktop,
  laptop, mobile, server, or other?
- How does the system behave when the `since` timestamp is malformed, in the
  future, or older than available update history?
- What happens when update collections are empty but the client still needs a new
  timestamp for later synchronization?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST treat devices as account-scoped client identities
  used throughout the API.
- **FR-002**: The system MUST store a device record with device ID, caption,
  device type, created-at timestamp, updated-at timestamp, owning user, and the
  current subscription count associated with that device.
- **FR-003**: A device ID MUST match the pattern `[\\w.-]+`.
- **FR-004**: Device IDs MUST be unique within a single user account, while the
  same identifier string MAY exist in a different user account.
- **FR-005**: The system MUST provide an authenticated contract compatible with
  `POST /api/2/devices/{username}/{deviceid}.json` to create or update a device
  for the targeted user.
- **FR-006**: The create-or-update contract MUST update only the fields supplied
  by the client and MUST leave unspecified mutable fields unchanged.
- **FR-007**: The create-or-update contract MUST accept caption as an optional
  human-readable device label.
- **FR-008**: The create-or-update contract MUST accept device type only when it
  is one of `desktop`, `laptop`, `mobile`, `server`, or `other`.
- **FR-009**: The system MUST reject create-or-update requests that target a
  username other than the authenticated user's account.
- **FR-010**: The system MUST provide an authenticated contract compatible with
  `GET /api/2/devices/{username}.json` that returns the targeted user's devices
  as a list of summaries containing device ID, caption, device type, and
  subscription count.
- **FR-011**: The list-devices contract MUST return only devices owned by the
  targeted user and MUST support an empty result when no devices exist.
- **FR-012**: The system MUST provide an authenticated contract compatible with
  `GET /api/2/updates/{username}/{deviceid}.json` for retrieving device-scoped
  synchronization changes.
- **FR-013**: The updates contract MUST return added subscriptions, removed
  subscription URLs, updated episodes, and a current timestamp that the client
  can reuse in a later request.
- **FR-014**: The updates contract MUST support an optional `since` value that
  narrows the response to changes after the supplied timestamp.
- **FR-015**: The updates contract MUST support an optional
  `include_actions` flag that adds the latest reported user action for each
  updated episode whose state is not `new`.
- **FR-016**: The updates contract MUST reject requests for unknown devices or
  devices not owned by the targeted authenticated user.
- **FR-017**: Subscription additions returned by the updates contract MUST
  include enough feed metadata for clients to subscribe without making another
  discovery request.
- **FR-018**: Episode updates returned by the updates contract MUST include the
  episode state, release timestamp, episode identity, and podcast identity needed
  for the client to reconcile local playback state.
- **FR-019**: The system MUST update device timestamps whenever a device record
  is created or its mutable device metadata changes.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence for this feature MUST include automated
  coverage for device identifier validation, account ownership checks, partial
  device updates, device listing behavior, incremental update retrieval, and
  optional action inclusion, plus manual validation of the three API contracts.
- **NFR-002**: Device and update contracts MUST avoid leaking another user's
  device existence, subscription set, or episode activity through authorization
  failures or cross-account access.
- **NFR-003**: Responses for list and update retrieval MUST remain predictable so
  compatible clients can process empty collections, partial updates, and repeated
  sync requests without ambiguity.
- **NFR-004**: The feature MUST preserve a simple device model centered on the
  documented fields and avoid requiring clients to manage additional registration
  steps beyond presenting a valid device ID and authentication context.

### Key Entities *(include if feature involves data)*

- **Device**: A client identity owned by one user account, defined by a
  client-generated device ID, an optional caption, a supported device type,
  lifecycle timestamps, and an associated subscription count.
- **Device Update Snapshot**: The set of additions, removals, episode changes,
  and timestamp returned to a device client for synchronization.
- **Episode Update**: A change to one episode's sync-relevant state, including
  episode identity, podcast identity, playback or download status, release
  information, and optionally the latest reported user action.
- **Subscription Summary**: The feed metadata returned when a device needs to add
  a subscription during synchronization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of requests with a device ID outside the allowed pattern are
  rejected without creating or updating a device record.
- **SC-002**: An authenticated user with up to 50 registered devices can receive
  a complete device list for their own account in a single request with no
  missing device summaries.
- **SC-003**: 100% of verified cross-account requests for device registration,
  listing, or updates are denied without exposing another user's device data.
- **SC-004**: A client that performs an initial update request and one follow-up
  request using the returned timestamp receives only new changes on the second
  call in at least 95% of validation scenarios.
- **SC-005**: 100% of updated episodes returned with `include_actions` enabled
  include the latest user action whenever the episode state is not `new`.

## Assumptions

- Device management in this feature is limited to create-or-update, list, and
  update retrieval; explicit device deletion is out of scope.
- Authentication already exists and reliably identifies the user account that is
  allowed to act on the targeted username.
- Subscription counts are derived from the current account-device relationship
  and are returned as part of the device summary contract.
- When a client creates a new device record without a caption, the system stores
  an empty caption rather than inventing a display label.
- The updates response uses the account's existing subscription and episode
  change history rather than introducing a separate manual synchronization queue.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: Device registration and listing each provide standalone
  value for compatible clients, while incremental updates add a higher-value sync
  slice without blocking validation of the first two contracts.
- **Branch Plan**: This feature is being specified on branch `005-device-api`,
  created from `main` in line with the constitution.
- **Verification Plan**: Before merge, the team must validate device ID rules,
  partial update behavior, supported device types, user ownership enforcement,
  empty and populated list responses, timestamp-based update filtering, optional
  action inclusion, and unauthorized access handling.
- **Quality Gate Strategy**: The implementation must satisfy lint, typing, and
  security checks by fixing root causes directly rather than suppressing findings
  with inline waivers.
- **Review Readiness**: The final pull request must summarize the delivered
  device contracts, the sync behaviors verified, account-ownership protections,
  and any device lifecycle scope intentionally deferred.
- **Security/Simplicity Notes**: Planning must justify how device ownership,
  timestamp-based update retrieval, and externally required response shapes stay
  secure and minimal without introducing unnecessary complexity.
