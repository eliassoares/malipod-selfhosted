# Feature Specification: User Authentication and Localized Profile

**Feature Branch**: `004-user-auth`
**Created**: 2026-04-15
**Status**: Draft
**Input**: User description: "Create the first user-facing account features for Malipod, including user registration, login, logout, a user profile page, multilingual behavior across English, Spanish, and Portuguese, and reusable shared page elements."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create an Account From the Website (Priority: P1)

As a new listener, I want to create a Malipod account from the website so I can
establish my public identity, set my language preference, and start using the
platform.

**Why this priority**: Registration is the first point of entry for new users
and unlocks all later authenticated experiences.

**Independent Test**: A new visitor can open the registration page on mobile or
desktop, submit valid account details, and receive a usable account without
needing the API directly.

**Acceptance Scenarios**:

1. **Given** a visitor opens the registration page, **When** they submit a
   unique email, a valid nickname, a password, and a supported language choice,
   **Then** the system creates the account and stores the chosen language as the
   user's preference.
2. **Given** a visitor submits a nickname shorter than 8 characters, longer than
   16 characters, or containing special characters, **When** they try to create
   the account, **Then** the system rejects the submission and explains the
   nickname rules.
3. **Given** a visitor submits an email or nickname already tied to an existing
   account, **When** they try to register, **Then** the system rejects the
   submission and informs them that the user already exists.

---

### User Story 2 - Sign In and Sign Out Across Web and API (Priority: P1)

As an existing user, I want to sign in and out reliably from the website and
from compatible API clients so I can access my account securely across devices.

**Why this priority**: Users with existing accounts need a dependable
authentication path before profile and personalization features have value.

**Independent Test**: An existing user can sign in successfully from the web,
sign in through the compatible API contract, receive an authenticated session,
and sign out again without exposing whether the email or password was wrong.

**Acceptance Scenarios**:

1. **Given** an existing user provides valid credentials on the website,
   **When** they sign in, **Then** the system authenticates them and redirects
   them to their profile page.
2. **Given** an API client calls the login contract for a specific username with
   valid credentials, **When** the request succeeds, **Then** the response
   establishes a session cookie for that same username.
3. **Given** a user provides an invalid email or incorrect password, **When**
   they attempt to sign in, **Then** the system responds with the generic message
   "login inválido" without revealing which field was incorrect.
4. **Given** a client presents a session cookie for a different username than
   the one targeted by the authentication contract, **When** it calls login or
   logout, **Then** the system rejects the request as a bad request.
5. **Given** a signed-in user or API client requests logout, **When** the
   request is processed, **Then** the active session is removed and the user is
   no longer authenticated.

---

### User Story 3 - Use a Localized Profile Experience (Priority: P2)

As a signed-in user, I want my profile and account pages to honor my language
preference across web visits so the product feels consistent and easier to use.

**Why this priority**: Personalization becomes meaningful once the user can sign
in and reach their own profile.

**Independent Test**: A signed-in user can reach their profile page by public
nickname, see the interface in their chosen supported language, and keep that
language consistent between visits through the website.

**Acceptance Scenarios**:

1. **Given** a signed-in user has a stored language preference, **When** they
   reach their profile page, **Then** the page content is rendered in that
   language.
2. **Given** a visitor or user selects a supported language on the website,
   **When** the site stores that choice, **Then** later account pages use the
   same language consistently through the site's cookie-based preference
   behavior.
3. **Given** a signed-in user lands on their authenticated web experience,
   **When** login succeeds, **Then** they are redirected to
   `/user/profile/{nickname}`.

## Edge Cases

- What happens when a visitor submits a nickname that is technically unique but
  violates the allowed public URL format?
- What happens when a visitor chooses an unsupported language code in a cookie or
  form submission?
- How does the website behave when a guest-language cookie conflicts with the
  stored language preference of an authenticated user?
- What happens when an API client attempts to log in without credentials?
- What happens when a user tries to open a profile URL for a deactivated account?
- How does the site respond when a session is expired but the user tries to open
  the profile page directly?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST store a user record with nickname, password
  credential, email, picture URL, language preference, created-at timestamp,
  updated-at timestamp, last-accessed timestamp, and deactivated-at timestamp.
- **FR-002**: The system MUST initialize the language preference to English by
  default when the user has not chosen another supported language.
- **FR-003**: The system MUST provide a website registration flow based on the
  supplied registration design and adapt it so it remains usable on both mobile
  and desktop layouts.
- **FR-004**: The registration flow MUST create an account only when the
  nickname is 8 to 16 characters long, contains no special characters, and is
  safe to use in public URLs.
- **FR-005**: The registration flow MUST reject attempts to create a user whose
  email or nickname already belongs to an existing account and MUST inform the
  user that the user already exists.
- **FR-006**: The registration flow MUST be available through the website and
  MUST NOT be exposed as a public API endpoint.
- **FR-007**: The system MUST provide a sign-in experience on the website based
  on the supplied login design and adapt it so it remains usable on both mobile
  and desktop layouts.
- **FR-008**: The system MUST provide an API login contract compatible with
  `POST /api/2/auth/{username}/login.json`, using HTTP Basic authentication for
  the targeted username and establishing a session cookie when authentication
  succeeds.
- **FR-009**: The API login contract MUST respond as unauthorized when called
  without credentials and MUST respond as a bad request when the client presents
  a cookie for a different username than the one named in the request.
- **FR-010**: The system MUST provide an API logout contract compatible with
  `POST /api/2/auth/{username}/logout.json` and remove the active session for
  the targeted user when logout succeeds.
- **FR-011**: The API logout contract MUST return success when no cookie is sent
  and MUST return a bad request when the client presents a cookie for a
  different username than the one named in the request.
- **FR-012**: When sign-in fails because the email is invalid or the password is
  incorrect, the system MUST return only the generic failure message
  "login inválido".
- **FR-013**: Successful website sign-in MUST redirect the user to their profile
  URL using the pattern `/user/profile/{nickname}`.
- **FR-014**: The system MUST provide a website-only user profile page based on
  the supplied profile design and adapt it so it remains usable on both mobile
  and desktop layouts.
- **FR-015**: The website MUST support English, Spanish, and Portuguese across
  registration, sign-in, sign-out, and profile experiences.
- **FR-016**: The website MUST remember a visitor's selected language by cookie
  and MUST reconcile that choice with the authenticated user's stored language
  preference so authenticated experiences stay consistent.
- **FR-017**: Once a user is authenticated, the website MUST prioritize the
  user's stored language preference for account pages and keep the cookie-aligned
  experience consistent for later visits.
- **FR-018**: Shared visual and structural elements common to registration,
  login, and profile pages MUST be extracted into reusable page components or
  templates rather than duplicated independently.
- **FR-019**: The system MUST update the relevant account timestamps when a user
  is created, authenticated, or otherwise changes account details relevant to
  the feature.

### Non-Functional Requirements *(mandatory)*

- **NFR-001**: Verification evidence for this feature MUST include automated
  coverage for account creation rules, duplicate-account rejection, login/logout
  contract behavior, localized page behavior, and authenticated redirect flows,
  plus manual checks of registration, login, and profile pages on mobile and
  desktop layouts.
- **NFR-002**: Authentication-related responses MUST minimize account
  enumeration risk by using generic failure messaging for invalid login attempts
  and by avoiding exposure of password details through routine errors.
- **NFR-003**: Multilingual account pages MUST keep visible text translatable,
  present the correct document language for the rendered locale, and preserve a
  consistent supported-language experience across account flows.
- **NFR-004**: The first account feature set MUST reuse shared page structure and
  avoid unnecessary duplication so future authenticated pages can extend the same
  layout and localization patterns.

### Key Entities *(include if feature involves data)*

- **User**: A person with a unique public nickname, a unique email, stored
  authentication credentials, an optional profile image, a preferred language,
  lifecycle timestamps, and an optional deactivation timestamp.
- **Authenticated Session**: The active signed-in state tied to a specific user
  and device context, used by both website interactions and compatible API
  requests.
- **Language Preference**: The user's selected supported language for account
  pages, derived from explicit choice and reinforced through stored account
  preference and cookie-based website continuity.
- **Profile URL Identity**: The public account path derived from the user's
  valid nickname and used to locate the website profile page.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new visitor can complete account creation from the website in
  under 2 minutes on both a narrow mobile viewport and a desktop viewport.
- **SC-002**: 100% of registration attempts using duplicate email or duplicate
  nickname receive a clear rejection instead of creating a second account.
- **SC-003**: 100% of invalid sign-in attempts return the same generic login
  failure message without exposing whether the email or password caused the
  failure.
- **SC-004**: Supported-language account pages render in the user's selected or
  stored language in at least 95% of tested repeat visits across registration,
  sign-in, and profile flows.
- **SC-005**: A successfully authenticated website user reaches their profile
  page in a single post-login redirect with no manual navigation required.

## Assumptions

- Email is required for account registration because the requested login flow
  explicitly distinguishes invalid email handling.
- Nickname and email are both unique across active user accounts.
- The profile page in this feature is limited to authenticated website access and
  does not yet expose an editable public profile API.
- Supported languages for this increment are limited to English, Spanish, and
  Portuguese, with English as the fallback when neither a valid cookie nor a
  stored user preference is available.
- The website's language selector is available on the relevant account pages and
  represents an explicit user choice rather than passive browser detection alone.

## Constitution Alignment *(mandatory)*

- **Slice Integrity**: Registration and login/logout each deliver standalone user
  value, while the localized profile experience builds on authenticated access
  without preventing the earlier slices from being validated independently.
- **Branch Plan**: This feature is being specified on branch `004-user-auth`,
  created from `main` in line with the constitution.
- **Verification Plan**: Before merge, the team must validate account creation
  rules, duplicate-user handling, sign-in and sign-out behavior for website and
  API flows, session-cookie behavior, generic invalid-login responses, localized
  rendering, and responsive layout behavior on mobile and desktop.
- **Quality Gate Strategy**: The implementation must resolve lint, typing, and
  security issues directly rather than suppressing them with `# noqa`, `# nosec`,
  or similar inline shortcuts.
- **Review Readiness**: The final pull request must summarize delivered account
  capabilities, the registration/login/profile scenarios verified, multilingual
  behavior tested, and any deferred account-management scope.
- **Security/Simplicity Notes**: Planning must justify how password handling,
  session behavior, duplicate-account checks, locale persistence, and reusable
  page structure stay secure and minimal without introducing unnecessary
  abstraction.
