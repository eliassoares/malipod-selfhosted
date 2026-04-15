# Research: User Authentication and Localized Profile

## Decision: Keep a single FastAPI application for both auth API and auth pages

**Rationale**: The project already has a single FastAPI runtime serving both
HTML and JSON. Extending that runtime with account routes preserves one security
boundary, one configuration model, one template environment, and one database
session pattern. This satisfies the feature without introducing coordination
cost between separate services.

**Alternatives considered**:
- Separate auth service: clearer service boundaries later, but unnecessary
  operational complexity for the first account increment.
- API-only auth with a separate frontend app: not aligned with the current
  server-rendered foundation and would add a second delivery surface too early.

## Decision: Use database-backed sessions instead of cookie-only sessions

**Rationale**: The requested login/logout contract explicitly says logout
removes the session ID from the database. That makes a server-side session table
the simplest compliant design. The web and API flows can share one session
model, one cookie name, and one invalidation path.

**Alternatives considered**:
- Starlette signed session cookie only: simpler wiring, but cannot remove a
  server-tracked session ID from the database on logout.
- Stateless bearer tokens: powerful later, but outside the requested contract
  and unnecessarily broad for this first auth slice.

## Decision: Use HTTP Basic only for the compatibility API login contract

**Rationale**: The requested API contract explicitly uses HTTP Basic Auth for
`POST /api/2/auth/{username}/login.json`. Keeping Basic limited to that contract
preserves compatibility while the website uses standard form submission and the
server translates successful authentication into the shared session-cookie model.

**Alternatives considered**:
- Use HTTP Basic for the website too: poor browser UX and not aligned with the
  supplied login page flow.
- Replace Basic with JSON credentials for the API: simpler modern API shape, but
  breaks the requested compatibility contract.

## Decision: Derive password hashes with Python's standard-library key-derivation APIs

**Rationale**: The project currently avoids extra auth dependencies and the user
requested pinned libraries with a security focus. Python's `hashlib` provides
password-oriented key derivation and explicitly warns that naive hashing is not
appropriate for passwords. A standard-library PBKDF2-based scheme with per-user
random salts keeps the stack small and secure enough for this phase.

**Alternatives considered**:
- Add Passlib or Argon2 dependencies: viable and often ergonomic, but they add
  more third-party surface area than this feature strictly needs.
- Store raw passwords or simple SHA hashes: unacceptable from a security
  perspective.

## Decision: Resolve locale with explicit precedence: authenticated user preference, then cookie, then default

**Rationale**: The feature requires both cookie-based preference continuity and
stored per-user `language_preference`. The least surprising behavior is to let
an authenticated user's stored preference win on account pages, sync the cookie
to that value, and fall back to a supported guest cookie or English default when
no authenticated preference exists.

**Alternatives considered**:
- Cookie always wins: causes authenticated pages to drift away from the user's
  stored preference.
- Browser `Accept-Language` always wins: weak for explicit user intent and less
  predictable across repeat visits.

## Decision: Keep localization server-rendered with translation keys and shared layout partials

**Rationale**: The current product already uses Jinja2 templates. For the first
set of account pages, the smallest maintainable option is to centralize visible
strings behind translation keys, render the correct document `lang` attribute,
and share common layout elements through a base template and partials. This
supports the mobile-first designs while preventing string duplication across
pages.

**Alternatives considered**:
- Hard-code translated strings independently in each template: fastest short
  term, but fragile and difficult to keep consistent.
- Introduce a full external localization platform now: useful later, but too
  much process and tooling for three supported locales and a few initial pages.

## Decision: Validate nickname as both identity and URL slug at account-creation time

**Rationale**: The nickname is used in profile URLs and the spec requires 8 to
16 characters with no special characters. Validating against a conservative
ASCII slug pattern at creation time avoids later routing ambiguity and keeps the
public identity stable.

**Alternatives considered**:
- Allow free-form display names plus separate slug: more flexible, but not part
  of the requested model.
- Permit broader Unicode nicknames immediately: possible later, but creates more
  URL and normalization complexity for the first implementation.

## Decision: Use reusable page partials and a shared base template for the auth/profile pages

**Rationale**: The supplied designs share recurring elements such as branding,
language selection, footer content, and page chrome. Pulling those pieces into a
common base template and partials reduces duplication and gives later account
pages a consistent place to hook into localization and session context.

**Alternatives considered**:
- Copy each page layout independently: easiest for the first commit, but
  increases maintenance cost immediately.
- Build a full component system or frontend framework: more structure than the
  current server-rendered architecture requires.
