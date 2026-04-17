# Feature Specification: Podcast Lists API

**Feature Branch**: `008-podcast-lists-api`
**Created**: 2026-04-16
**Status**: Draft
**Input**: User description: "Vamos desenvolver a api de Podcast Lists. Podcast Lists are used to collect podcasts about one topic. On the website, podcast lists are available at https://gpodder.net/lists/. Create Podcast List: POST /api/2/lists/(username)/create.(format). Get User's Lists: GET /api/2/lists/(username).json. Get a Podcast List: GET /api/2/lists/(username)/list/(listname).(format). Update a Podcast List: PUT /api/2/lists/(username)/list/(listname).(format). Delete a Podcast List: DELETE /api/2/lists/(username)/list/(listname).(format)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse and Read Podcast Lists (Priority: P1)

As a podcast listener, I want to view a user's available podcast lists and open
one specific list so I can discover curated podcast collections around a topic.

**Why this priority**: Reading lists is the main user-facing value of the
feature because curated collections are useful even before a user creates or
edits their own lists.

**Independent Test**: A client can retrieve a user's list summaries in JSON and
request one named list in a supported format, while unknown users or missing
lists return the documented not-found responses.

**Acceptance Scenarios**:

1. **Given** a user owns one or more podcast lists, **When** a client requests
   that user's list summaries, **Then** the service returns each list's title,
   generated name, and public web URL.
2. **Given** a named podcast list exists for a user, **When** a client requests
   that list in a supported format, **Then** the service returns the list
   content in the requested format.
3. **Given** a client requests lists for a username that does not exist,
   **When** the request is processed, **Then** the service returns `404 Not
   Found`.
4. **Given** a client requests a list name that does not exist for the targeted
   user, **When** the request is processed, **Then** the service returns `404
   Not Found`.

---

### User Story 2 - Create a Podcast List (Priority: P1)

As an authenticated user, I want to create a new podcast list from a title and
list content so I can publish a curated set of podcasts under my account.

**Why this priority**: Creation is the core write path that turns this feature
into a usable publishing surface instead of a read-only catalog.

**Independent Test**: An authenticated user can submit a title plus list
content in a supported format and receive a redirect to the newly created list,
while duplicate generated names and cross-account attempts are rejected.

**Acceptance Scenarios**:

1. **Given** an authenticated user submits a valid title and valid list content
   for their own account, **When** the create request is processed, **Then**
   the service creates a new podcast list, generates a short name from the
   title, and returns `303 See Other` with the new list URL in the `Location`
   header.
2. **Given** an authenticated user submits a title whose generated short name
   matches an existing list they already own, **When** the create request is
   processed, **Then** the service returns `409 Conflict` and does not create a
   duplicate list.
3. **Given** an authenticated user targets another username, **When** the
   create request is processed, **Then** the service rejects the request and
   does not create a list.
4. **Given** an authenticated user creates a list with a human-readable title,
   **When** the list is created, **Then** the generated name is stable,
   URL-safe, and derived predictably from that title.

---

### User Story 3 - Maintain an Existing Podcast List (Priority: P2)

As an authenticated user, I want to update or delete one of my existing podcast
lists so I can keep its contents current or remove a list that is no longer
useful.

**Why this priority**: Ongoing maintenance is important after creation, but the
feature still delivers value if users can only browse and create lists in the
first release.

**Independent Test**: An authenticated user can replace the content of an
existing list or delete it entirely, while requests for missing lists or other
users' lists are rejected.

**Acceptance Scenarios**:

1. **Given** an authenticated user owns a named podcast list, **When** they
   upload replacement content for that list in a supported format, **Then** the
   service updates the stored list and returns `204 No Content`.
2. **Given** an authenticated user owns a named podcast list, **When** they
   delete that list, **Then** the service removes it and returns `204 No
   Content`.
3. **Given** an authenticated user tries to update or delete a list that does
   not exist, **When** the request is processed, **Then** the service returns
   `404 Not Found`.
4. **Given** an authenticated user tries to update or delete a list belonging
   to another user, **When** the request is processed, **Then** the service
   rejects the request.

### Edge Cases

- What happens when a list title normalizes into an empty or nearly empty short
  name after removing unsupported characters?
- How does the service behave when two different titles normalize to the same
  generated name for the same user?
- What happens when a create or update request contains zero podcast entries?
- How does the service respond when the request body cannot be parsed in the
  format indicated by the URL extension?
- What happens when list content includes duplicate podcast entries or invalid
  feed URLs?
- How does deletion behave when a client repeats the same delete request after
  the list was already removed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a contract compatible with
  `POST /api/2/lists/{username}/create.{format}` for creating a podcast list for
  one authenticated user account.
- **FR-002**: The create contract MUST require authentication and MUST reject
  requests that target a username other than the authenticated user's account.
- **FR-003**: The create contract MUST accept a URL-encoded title parameter and
  list content in the request body using the format indicated by the URL
  extension.
- **FR-004**: The system MUST generate a short list name from the submitted
  title using a predictable URL-safe normalization process.
- **FR-005**: When the generated short name already exists for that same user,
  the create contract MUST return `409 Conflict` and MUST NOT create a second
  list with that name.
- **FR-006**: When a list is created successfully, the create contract MUST
  return `303 See Other` and include the canonical URL of the new list in the
  `Location` header.
- **FR-007**: The system MUST provide a contract compatible with
  `GET /api/2/lists/{username}.json` for retrieving the summaries of all lists
  owned by a user.
- **FR-008**: The user-lists summary contract MUST return a JSON array where
  each item includes the list title, generated name, and public web URL.
- **FR-009**: The user-lists summary contract MUST return `404 Not Found` when
  the targeted username does not exist.
- **FR-010**: The system MUST provide a contract compatible with
  `GET /api/2/lists/{username}/list/{listname}.{format}` for retrieving the
  contents of one named podcast list in a supported format.
- **FR-011**: The list-read contract MUST return `404 Not Found` when either
  the targeted username or the named list does not exist.
- **FR-012**: The system MUST provide a contract compatible with
  `PUT /api/2/lists/{username}/list/{listname}.{format}` for replacing the
  contents of one named podcast list.
- **FR-013**: The update contract MUST require authentication and MUST reject
  requests that target a username other than the authenticated user's account.
- **FR-014**: When the targeted list exists and the submitted content is valid,
  the update contract MUST replace the stored list content and return
  `204 No Content`.
- **FR-015**: The update contract MUST return `404 Not Found` when either the
  targeted username or the named list does not exist.
- **FR-016**: The system MUST provide a contract compatible with
  `DELETE /api/2/lists/{username}/list/{listname}.{format}` for deleting one
  named podcast list.
- **FR-017**: The delete contract MUST require authentication and MUST reject
  requests that target a username other than the authenticated user's account.
- **FR-018**: When the targeted list exists, the delete contract MUST remove it
  and return `204 No Content`.
- **FR-019**: The delete contract MUST return `404 Not Found` when either the
  targeted username or the named list does not exist.
- **FR-020**: All read, create, and update operations in this feature MUST use
  the externally supported podcast-list formats consistently for request
  parsing and response rendering.
- **FR-021**: The system MUST preserve the list title separately from the
  generated name so users can see a human-readable label while clients address
  the canonical short name.
- **FR-022**: The service MUST preserve a predictable ordering for a user's
  list summaries so clients and the website can render curated collections
  consistently.
- **FR-023**: The feature MUST treat podcast lists as user-owned resources and
  MUST NOT expose private write access across accounts.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence for this feature MUST include automated
  coverage for successful creation, generated-name conflicts, user-list
  summaries, list retrieval, update success, delete success, cross-account
  denial, not-found responses, and invalid body parsing, plus manual validation
  of the five list API contracts.
- **NFR-002**: Podcast list write endpoints MUST avoid leaking whether another
  user's resources can be modified through cross-account requests.
- **NFR-003**: Generated names, redirect destinations, and list summary payloads
  MUST remain stable enough for compatible clients and the website to link to
  the same list consistently over time.
- **NFR-004**: The feature MUST extend the existing podcast domain with the
  simplest list-management behavior that satisfies the documented contracts
  without adding unnecessary user-facing scope.

### Key Entities *(include if feature involves data)*

- **Podcast List**: A user-owned curated collection of podcasts grouped under a
  human-readable title and a generated canonical name.
- **Podcast List Entry**: One podcast reference included in a list's stored
  content and returned in supported read formats.
- **Podcast List Summary**: The compact representation of a user's list that
  includes title, canonical name, and public web URL.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of validated create requests for unique titles return
  `303 See Other` with a `Location` header that resolves to the created list.
- **SC-002**: 100% of validated create requests whose generated names collide
  with an existing list owned by the same user return `409 Conflict` and leave
  the existing list unchanged.
- **SC-003**: 100% of validated requests for a known user's list summaries
  return only that user's list metadata and no lists from another account.
- **SC-004**: 100% of validated update and delete requests for owned lists
  return `204 No Content` and leave the targeted resource in the requested
  final state.
- **SC-005**: 100% of validated requests for missing users or missing lists
  return `404 Not Found` across read, update, and delete flows.

## Assumptions

- Authentication already exists and reliably identifies which user account is
  allowed to create, update, or delete lists for a targeted username.
- Supported podcast-list formats follow the service's broader format
  conventions, and this feature reuses those same supported formats rather than
  introducing a new custom format just for lists.
- A podcast list may contain zero or more podcast references, and an empty list
  is allowed unless later clarification or contract research proves otherwise.
- The generated canonical name is derived only from the submitted title and is
  unique within one user's account rather than globally across all users.
- The public web URL for each list follows the website pattern shown in the
  request description and remains derivable from the owning username and
  canonical list name.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: Reading public list data, creating new lists, and
  maintaining existing lists remain independently valuable slices that can be
  tested and demonstrated in priority order.
- **Branch Plan**: This feature is being specified on branch
  `008-podcast-lists-api`, created from `main` in line with the constitution.
- **Verification Plan**: Before merge, the team must validate generated-name
  creation, conflict handling, summary responses, list reads, update/delete
  flows, format-driven parsing, not-found behavior, and cross-account access
  denial.
- **Quality Gate Strategy**: The implementation must satisfy lint, typing, and
  security checks by fixing root causes directly rather than suppressing
  findings with inline waivers.
- **Review Readiness**: The final pull request must summarize the delivered
  list contracts, ownership rules, generated-name behavior, and any deferred
  decisions about list-content formats or validation rules.
- **Security/Simplicity Notes**: Planning must justify how generated-name
  normalization, ownership checks, format handling, and redirect behavior remain
  secure and minimal without introducing unnecessary complexity.
