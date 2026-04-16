# Feature Specification: Subscriptions API

**Feature Branch**: `006-subscriptions-api`
**Created**: 2026-04-15
**Status**: Draft
**Input**: User description: "Vamos desenvolver a api de Subscriptions. Podcast is identified by its feed URL, episode is identified by its media URL. Endpoints: Get Subscriptions of Device, Get All Subscriptions, Upload Subscriptions of Device, Upload Subscription Changes, Get Subscription Changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Account and Device Subscriptions (Priority: P1)

As an authenticated podcast client, I want to retrieve subscription lists for a
specific device or for the whole account so I can bootstrap the local podcast
catalog when the app starts or when I switch devices.

**Why this priority**: Clients need a reliable read path before they can
synchronize or repair local state, and the account-wide list is especially
important for first-run onboarding.

**Independent Test**: An authenticated client can request subscriptions for a
known device or for the whole account in a supported format and receive the
expected feed URLs, while invalid devices and unsupported formats are rejected
with the documented status codes.

**Acceptance Scenarios**:

1. **Given** an authenticated user has subscriptions associated with a known
   device, **When** the client requests the device subscriptions in a supported
   format, **Then** the system returns that device's subscriptions in the
   requested format.
2. **Given** an authenticated user has subscriptions across one or more
   devices, **When** the client requests all subscriptions for the account,
   **Then** the system returns the account-wide subscription set in the
   requested format.
3. **Given** an authenticated client requests subscriptions for a device ID that
   does not belong to the targeted user, **When** the request is processed,
   **Then** the system returns the documented invalid-device response instead of
   exposing another user's subscriptions.
4. **Given** an authenticated client requests a format the service does not
   support, **When** the request is processed, **Then** the system returns the
   documented invalid-format response.

---

### User Story 2 - Replace a Device Subscription List (Priority: P1)

As an authenticated podcast client, I want to upload the current full
subscription list for one device so the server can store the device state even
when the device is new or after a full local refresh.

**Why this priority**: Full-device uploads provide the recovery and first-sync
path that many clients need before delta-based sync becomes useful.

**Independent Test**: An authenticated client can upload a complete
subscription list for a device in a supported input format, receive an empty
successful response body, and observe that a missing device is created
automatically for that account.

**Acceptance Scenarios**:

1. **Given** an authenticated client uploads a valid full subscription list for
   an existing device in a supported format, **When** the request is processed,
   **Then** the server replaces that device's stored subscription list and
   returns status `200` with an empty body.
2. **Given** an authenticated client uploads a valid full subscription list for
   a device that does not yet exist for the targeted user, **When** the request
   is processed, **Then** the server creates the device automatically and stores
   the uploaded subscriptions for it.
3. **Given** an authenticated client uploads a payload in an unsupported format,
   **When** the request is processed, **Then** the server returns the documented
   invalid-format response and does not change the stored subscriptions.
4. **Given** an authenticated client targets another user's username, **When**
   the upload is processed, **Then** the server rejects the request.

---

### User Story 3 - Sync Subscription Changes Incrementally (Priority: P2)

As an authenticated podcast client, I want to exchange subscription deltas with
the server so I can keep a device synchronized efficiently without uploading or
downloading the entire subscription list every time.

**Why this priority**: Incremental synchronization is the higher-value ongoing
sync path once bootstrap and full replacement behavior already exist.

**Independent Test**: An authenticated client can upload add/remove deltas,
receive a new server timestamp plus any rewritten URLs, and later request
subscription changes since a previous timestamp to get only newer additions and
removals.

**Acceptance Scenarios**:

1. **Given** an authenticated client uploads subscription deltas with separate
   add and remove lists, **When** the request is processed, **Then** the server
   applies the changes, returns a new timestamp, and includes any rewritten
   feed URLs.
2. **Given** an authenticated client includes the same feed URL in both add and
   remove within one delta request, **When** the request is processed, **Then**
   the server rejects the request as invalid.
3. **Given** an authenticated client requests changes since a prior timestamp,
   **When** newer subscription changes exist for that device, **Then** the
   server returns only the additions and removals after that timestamp plus a
   fresh timestamp for the next request.
4. **Given** an authenticated client requests changes since a prior timestamp
   and nothing has changed, **When** the request is processed, **Then** the
   server returns empty add and remove lists plus a fresh timestamp.
5. **Given** a delta request contains URLs that are not allowed, **When** the
   request is processed, **Then** the server rewrites them to empty strings,
   ignores them semantically, and reports the rewrite results in `update_urls`.

## Edge Cases

- What happens when a device subscription request uses a valid username but a
  device that exists under a different user account?
- How does the service behave when a supported format payload contains duplicate
  feed URLs in the same upload?
- What happens when a full upload contains zero subscriptions for a device?
- How does the service respond when the `since` value is missing, malformed,
  negative, or older than the retained subscription-change history?
- What happens when URL sanitation rewrites a feed URL to the empty string?
- How does the service handle a device delta upload that includes subscriptions
  already present or removals for subscriptions that are already absent?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST identify each podcast subscription by its feed
  URL.
- **FR-002**: The system MUST provide an authenticated contract compatible with
  `GET /subscriptions/{username}/{deviceid}.{format}` for retrieving the
  subscriptions of one device.
- **FR-003**: The device-subscriptions read contract MUST support the externally
  required formats for this feature: OPML, JSON, and plaintext, plus JSONP where
  the selected format allows it.
- **FR-004**: The device-subscriptions read contract MUST return `404` when the
  device ID is invalid for the targeted user and MUST return `400` when the
  requested format is invalid.
- **FR-005**: The system MUST provide an authenticated contract compatible with
  `GET /subscriptions/{username}.{format}` for retrieving all subscriptions
  belonging to the targeted user account.
- **FR-006**: The account-wide read contract MUST return the user's complete
  subscription set regardless of device grouping and MUST return `400` when the
  requested format is invalid.
- **FR-007**: The system MUST provide an authenticated contract compatible with
  `PUT /subscriptions/{username}/{deviceid}.{format}` for uploading the current
  full subscription list of one device.
- **FR-008**: The full-upload contract MUST accept OPML, JSON, and plaintext
  request bodies representing the current subscriptions for that device.
- **FR-009**: The full-upload contract MUST replace the device's stored
  subscription list with the uploaded list and MUST return status `200` with an
  empty response body on success.
- **FR-010**: When the targeted device does not exist for the user, the
  full-upload contract MUST create that device automatically before storing the
  uploaded subscriptions.
- **FR-011**: The system MUST provide an authenticated contract compatible with
  `POST /api/2/subscriptions/{username}/{deviceid}.json` for uploading
  subscription deltas.
- **FR-012**: The delta-upload contract MUST reject a request as `400` when the
  same feed URL appears in both the add and remove lists of the same request.
- **FR-013**: The delta-upload contract MUST return a server-issued timestamp
  and an `update_urls` collection describing any feed URLs that were rewritten.
- **FR-014**: The system MUST sanitize subscription URLs during delta upload,
  rewriting unsupported URLs to the empty string and ignoring them semantically.
- **FR-015**: The system MUST provide an authenticated contract compatible with
  `GET /api/2/subscriptions/{username}/{deviceid}.json` for retrieving
  subscription changes since a supplied timestamp.
- **FR-016**: The delta-read contract MUST accept a `since` query parameter and
  return add and remove lists containing only changes after that timestamp, plus
  a fresh timestamp for the next request.
- **FR-017**: When there are no subscription changes after the supplied
  timestamp, the delta-read contract MUST still return empty add and remove
  lists plus a fresh timestamp.
- **FR-018**: All subscriptions contracts in this feature MUST reject requests
  that target a username other than the authenticated user's account.
- **FR-019**: The service MUST preserve predictable ordering and de-duplicated
  subscription values in responses so compatible clients can reconcile local
  state deterministically.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence for this feature MUST include automated
  coverage for supported-format reads, full-upload replacement behavior,
  auto-created devices during full upload, delta validation, URL sanitation,
  `since` filtering, and account-ownership enforcement, plus manual validation
  of the five API contracts.
- **NFR-002**: Subscription endpoints MUST avoid leaking another user's
  subscriptions, device existence, or change history through cross-account
  requests.
- **NFR-003**: Response payloads and supported formats MUST remain stable enough
  for compatible clients to parse first-run reads, full uploads, and repeated
  delta synchronization without ambiguity.
- **NFR-004**: The feature MUST extend the existing devices and podcast domain
  with the simplest persistence and change-tracking approach that satisfies the
  documented contracts without introducing unnecessary infrastructure layers.

### Key Entities *(include if feature involves data)*

- **Subscription**: A podcast feed reference identified by one feed URL and
  optionally associated with metadata needed for supported output formats.
- **Device Subscription Set**: The complete subscription list currently stored
  for one device under one user account.
- **Subscription Change Set**: The add/remove delta recorded for one device sync
  window and identified by a server-issued timestamp.
- **URL Rewrite Result**: The original and sanitized feed URL pair returned to a
  client when the service rewrites a subscription URL.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of validated reads for supported subscription formats return
  the expected device or account-wide feed URLs without mixing data from another
  user.
- **SC-002**: 100% of successful full-device uploads return status `200` with an
  empty body and leave the stored device subscriptions matching the uploaded
  list.
- **SC-003**: 100% of verified delta uploads that add and remove the same feed
  URL in one request are rejected as invalid.
- **SC-004**: A client that stores the returned timestamp and performs a
  subsequent delta-read request receives only newer subscription changes in at
  least 95% of validation scenarios.
- **SC-005**: 100% of sanitized invalid URLs in delta uploads are reported back
  through `update_urls` and are not applied as active subscriptions.

## Assumptions

- Authentication already exists and reliably identifies the user account allowed
  to act on the targeted username.
- Device creation for this feature is limited to the automatic creation required
  by the full-upload contract; separate explicit device-management behavior
  remains in the devices feature.
- Supported subscription formats for this increment are OPML, JSON, and
  plaintext for uploads and reads, with JSONP available only where the chosen
  output format supports it.
- Account-wide subscription reads return the de-duplicated union of the user's
  stored subscriptions across devices.
- Episode identity by media URL matters to the wider product domain, but this
  feature is scoped only to subscription synchronization rather than episode
  state updates.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: Read contracts, full-device replacement, and incremental
  delta synchronization each provide standalone client value and can be tested
  independently in priority order.
- **Branch Plan**: This feature is being specified on branch
  `006-subscriptions-api`, created from `main` in line with the constitution.
- **Verification Plan**: Before merge, the team must validate supported-format
  reads, invalid-format handling, auto-created devices during full upload,
  empty-body success responses, delta conflict rejection, URL rewrite reporting,
  timestamp-based change retrieval, and cross-account access denial.
- **Quality Gate Strategy**: The implementation must satisfy lint, typing, and
  security checks by fixing root causes directly rather than suppressing
  findings with inline waivers.
- **Review Readiness**: The final pull request must summarize the delivered
  subscriptions contracts, formats validated, synchronization behaviors tested,
  and any follow-up sync scope intentionally deferred.
- **Security/Simplicity Notes**: Planning must justify how supported-format
  parsing, device auto-creation during upload, URL sanitation, and timestamped
  delta history remain secure and minimal without introducing unnecessary
  complexity.
