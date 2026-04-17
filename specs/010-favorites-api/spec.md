# Feature Specification: Favorites API

**Feature Branch**: `010-favorites-api`
**Created**: 2026-04-17
**Status**: Draft
**Input**: User description: "Vamos desenvolver a api de favorites. Favorites API. Get Favorite Episodes: GET /api/2/favorites/(username).json. Requires Authentication. Since 2.4 (added released in 2.6). The response is a list of all favorite episodes, as they can be seen on http://gpodder.net/favorites/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read My Favorite Episodes (Priority: P1)

As an authenticated listener, I want to retrieve my favorite episodes in one
JSON response so I can synchronize my favorites list across clients.

**Why this priority**: Reading favorites is the core user value of this feature
and is the entire externally described contract.

**Independent Test**: An authenticated user can request
`GET /api/2/favorites/{username}.json` for their own account and receive a JSON
array containing each favorite episode with the documented metadata fields.

**Acceptance Scenarios**:

1. **Given** an authenticated user has one or more favorite episodes, **When**
   the user requests `GET /api/2/favorites/{username}.json`, **Then** the
   service returns a JSON array containing those favorite episodes.
2. **Given** an authenticated user has no favorite episodes, **When** the user
   requests `GET /api/2/favorites/{username}.json`, **Then** the service
   returns an empty JSON array.
3. **Given** an authenticated request is successful, **When** the response is
   returned, **Then** each favorite episode item includes title, episode URL,
   podcast title, podcast URL, description, website, released timestamp, and
   public link metadata.

---

### User Story 2 - Preserve Favorite Episode Metadata (Priority: P2)

As a client developer, I want each favorite episode to include consistent
podcast and episode details so I can render favorites without making additional
 lookup requests.

**Why this priority**: The API remains useful with basic favorite retrieval,
but consistent metadata makes the response practical for real client
applications.

**Independent Test**: A client can retrieve favorites and confirm that each
returned item preserves the expected episode and podcast metadata fields in a
stable, machine-readable shape.

**Acceptance Scenarios**:

1. **Given** a favorite episode has podcast and episode metadata available,
   **When** favorites are returned, **Then** the response preserves that
   metadata in the documented fields for that item.
2. **Given** an episode has a release timestamp, **When** it appears in the
   favorites response, **Then** the timestamp is returned in a machine-readable
   datetime format.
3. **Given** multiple favorites exist, **When** favorites are returned, **Then**
   the response ordering is stable enough for clients to reconcile repeated
   syncs predictably.

---

### User Story 3 - Protect Favorite Episode Access (Priority: P2)

As a product owner, I want the favorites API to require authentication and
respect account ownership so favorite episode data is not exposed across users.

**Why this priority**: Authentication and ownership checks protect private user
data, but the core retrieval flow still defines the main user-facing value.

**Independent Test**: Requests without authentication or for another user's
favorites are rejected, while valid requests for the authenticated user's own
favorites succeed.

**Acceptance Scenarios**:

1. **Given** a request omits valid authentication credentials, **When** the
   favorites endpoint is called, **Then** the service rejects the request.
2. **Given** an authenticated user requests another user's favorites, **When**
   the request is processed, **Then** the service rejects the request and does
   not expose the other user's favorite episodes.
3. **Given** an authenticated user requests favorites for a username that does
   not exist, **When** the request is processed, **Then** the service returns
   the documented not-found behavior.

### Edge Cases

- What happens when a favorite episode references podcast metadata that is only
  partially available?
- How does the service respond when a user has zero favorite episodes?
- What is returned when a favorite episode exists but one or more optional
  descriptive fields are missing?
- How are duplicate favorite markings for the same episode handled in the final
  response?
- What happens when a client requests favorites for a user that does not exist
  or is not the authenticated account?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide
  `GET /api/2/favorites/{username}.json` for retrieving favorite episodes.
- **FR-002**: The favorites endpoint MUST require authentication.
- **FR-003**: The system MUST reject requests where the authenticated account
  does not match the targeted username.
- **FR-004**: A successful favorites response MUST return a JSON array.
- **FR-005**: Each returned favorite episode item MUST include the episode
  title.
- **FR-006**: Each returned favorite episode item MUST include the episode URL.
- **FR-007**: Each returned favorite episode item MUST include the podcast
  title.
- **FR-008**: Each returned favorite episode item MUST include the podcast URL.
- **FR-009**: Each returned favorite episode item MUST include the episode
  description when that description is available.
- **FR-010**: Each returned favorite episode item MUST include the website URL
  when that value is available for the episode.
- **FR-011**: Each returned favorite episode item MUST include the released
  timestamp when that value is available for the episode.
- **FR-012**: Each returned favorite episode item MUST include the public link
  metadata for the episode when that value is available.
- **FR-013**: The system MUST return only episodes marked as favorites for the
  targeted authenticated user.
- **FR-014**: The system MUST NOT return duplicate entries for the same
  favorite episode in one response.
- **FR-015**: The system MUST return an empty JSON array when the authenticated
  user has no favorite episodes.
- **FR-016**: The system MUST return a not-found response when the targeted
  username does not exist.
- **FR-017**: The system MUST preserve a stable response ordering for favorite
  episodes so repeated syncs are predictable.
- **FR-018**: The system MUST expose favorite episodes in the same general view
  as the website favorites page, limited to the documented response fields.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence for this feature MUST include automated
  coverage for successful favorite retrieval, empty favorite lists,
  authentication failure, cross-account denial, not-found behavior, duplicate
  favorite handling, and metadata serialization.
- **NFR-002**: Favorite episode retrieval MUST protect user privacy by
  preventing one authenticated account from reading another account's favorites.
- **NFR-003**: The feature MUST satisfy the documented compatibility contract
  with the simplest retrieval behavior that reuses existing episode and user
  data instead of introducing unrelated social or recommendation features.

### Key Entities *(include if feature involves data)*

- **Favorite Episode**: One episode marked as a favorite for one user account
  and exposed through the favorites response.
- **Favorite Episode Response Item**: The serialized view of a favorite episode
  containing episode metadata plus its associated podcast metadata.
- **Favorite Episode Collection**: The ordered list of favorite episode items
  returned for one authenticated user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of validated authenticated requests for a user with favorite
  episodes return only that user's favorite episodes in JSON format.
- **SC-002**: 100% of validated authenticated requests for a user with no
  favorite episodes return an empty JSON array.
- **SC-003**: 100% of unauthenticated or cross-account requests are rejected
  without exposing favorite episode data.
- **SC-004**: 100% of returned favorite items include the documented identity
  and metadata fields when those values exist in the source episode data.
- **SC-005**: 100% of requests for missing usernames return the documented
  not-found behavior.

## Assumptions

- Existing authentication already identifies the requesting account and can be
  reused for this endpoint.
- Favorite status already exists in the product domain or can be derived from
  the current user-specific episode state without requiring a new end-user
  action in this feature.
- The response should stay read-only for this feature; creating or removing
  favorites is out of scope unless specified later.
- Missing optional metadata such as description, website, released timestamp,
  or public link may be returned as empty or null-compatible values rather than
  causing the whole item to be excluded.
- The endpoint returns only the authenticated user's own favorites and does not
  expose a public favorites feed for other accounts.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: Reading favorites, preserving favorite metadata, and
  enforcing access controls are independently valuable slices that can be
  implemented and demonstrated in priority order.
- **Branch Plan**: This feature is being specified on branch
  `010-favorites-api`, created from `main` in line with the constitution.
- **Verification Plan**: Before merge, the team must validate successful
  favorite reads, empty-list behavior, metadata serialization,
  authentication/ownership protection, duplicate handling, and missing-user
  responses.
- **Quality Gate Strategy**: The implementation must satisfy lint, typing, and
  security checks by fixing underlying issues directly instead of relying on
  inline suppressions.
- **Review Readiness**: The final pull request must summarize the favorites
  response contract, ownership rules, metadata mapping, verification coverage,
  and any assumptions about where favorite state is sourced.
- **Security/Simplicity Notes**: Planning must justify how favorite-state
  sourcing, ownership checks, and response ordering remain secure and minimal
  without expanding the feature into broader recommendation or social behavior.
