# Data Model: User Authentication and Localized Profile

## Overview

This feature introduces the first persistent user and session entities for
Malipod, plus the rules needed to resolve account identity, authentication
state, and supported-language continuity across website and API interactions.

## Entity: User

**Purpose**: Represents an individual Malipod account with public identity,
credentials, and account-level language preference.

**Fields**:
- `nickname`: public identifier used in profile URLs
- `password_hash`: derived password representation stored instead of the raw
  password
- `password_salt`: random salt associated with the password derivation
- `email`: unique account email used for sign-in
- `picture_url`: optional profile image location
- `language_preference`: supported locale code for authenticated account pages
- `created_at`: account creation timestamp
- `updated_at`: timestamp of the most recent account update
- `accessed_at`: timestamp of the most recent successful authenticated access
- `deactivated_at`: nullable timestamp for account deactivation

**Validation Rules**:
- `nickname` must be unique among active accounts
- `nickname` must match the public URL-safe format and remain 8 to 16
  characters long
- `email` must be unique among active accounts and valid for sign-in use
- `language_preference` must be one of `en`, `es`, or `pt-BR`
- `picture_url` may be null and, when present, must be a valid URL string
- `deactivated_at` is null for active accounts

**Relationships**:
- Has many `AuthenticatedSession` records
- Supplies the canonical language for authenticated website pages

## Entity: AuthenticatedSession

**Purpose**: Represents a server-tracked authenticated session bound to a
specific user and used to maintain website and compatibility API login state.

**Fields**:
- `session_id`: opaque session identifier stored in the cookie and persisted on
  the server
- `user_id`: owning account
- `created_at`: time the session was created
- `updated_at`: time the session was last refreshed
- `expires_at`: time after which the session is no longer valid
- `revoked_at`: nullable timestamp for logout or invalidation
- `user_agent`: optional client fingerprint summary for audit/debug use

**Validation Rules**:
- `session_id` must be globally unique and high-entropy
- `expires_at` must be later than `created_at`
- `revoked_at` is null for active sessions
- Active session cookies must only be accepted for the matching user named in
  the compatibility auth routes

**Relationships**:
- Belongs to one `User`
- Drives website authentication and API cookie validation

## Entity: LanguageSelectionContext

**Purpose**: Captures the resolved locale used to render account-related pages
for a request.

**Fields**:
- `requested_locale`: explicit locale submitted by the visitor or found in the
  cookie
- `effective_locale`: final locale used for rendering
- `source`: whether the locale came from authenticated user preference, cookie,
  or default fallback
- `is_supported`: whether the requested locale belongs to the approved set

**Validation Rules**:
- `effective_locale` must always be one of the supported languages
- Authenticated user preference takes precedence over guest cookie state on
  authenticated account pages

**Relationships**:
- May depend on `User`
- Influences rendered templates and response cookies

## Entity: RegistrationSubmission

**Purpose**: Represents the website-only data submitted during account creation.

**Fields**:
- `nickname`
- `email`
- `password`
- `password_confirmation`
- `picture_url`
- `language_preference`

**Validation Rules**:
- `nickname` must satisfy the public identity rules
- `email` must be syntactically valid and not already in use
- `password` and `password_confirmation` must match
- `language_preference` defaults to English when omitted or invalid

**Relationships**:
- Creates one `User` on success

## State Transitions

### User Lifecycle

- `pending submission` → `active`: valid registration creates the user
- `active` → `active`: successful login updates `accessed_at`
- `active` → `deactivated`: deactivation sets `deactivated_at`

### Session Lifecycle

- `new` → `active`: valid login creates a persisted session
- `active` → `active`: valid reuse refreshes session activity metadata
- `active` → `revoked`: logout sets `revoked_at` and removes validity
- `active` → `expired`: session passes `expires_at`

## Future Extension Notes

This model intentionally leaves room for later additions such as password reset
tokens, email verification records, podcast subscriptions, and per-device sync
metadata without changing the core user/session boundary introduced here.
