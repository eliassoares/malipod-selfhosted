# Quickstart: User Authentication and Localized Profile

## Goal

Run the new account flows locally, verify website and API authentication
behavior, and confirm multilingual account pages behave consistently before
opening a pull request.

## Prerequisites

- Docker and Docker Compose available locally
- Project dependencies installed with the pinned toolchain
- Existing foundation setup already working from the previous feature

## 1. Prepare configuration

1. Ensure your local environment file exists:

   ```bash
   cp .env.example .env
   ```

2. Confirm the application secret and database settings are present.
3. Use development-only credentials and secrets locally.

## 2. Start the application

1. Start the stack:

   ```bash
   docker compose up --build
   ```

2. Wait for the application and PostgreSQL service to report healthy.
3. Open the home page at [http://localhost:8000/](http://localhost:8000/).

## 3. Verify registration and profile flows

1. Open the registration page in a browser.
2. Confirm the page is usable on both a mobile-width viewport and a desktop
   viewport.
3. Create a new account using a valid nickname, unique email, password, and one
   supported language.
4. Confirm duplicate email and duplicate nickname attempts are rejected.
5. Confirm an invalid nickname is rejected with clear guidance.

## 4. Verify login and logout

1. Open the website login page and sign in with the newly created account.
2. Confirm successful login redirects to `/user/profile/{nickname}`.
3. Confirm an incorrect email or incorrect password produces the generic failure
   message only.
4. Call the API login contract with HTTP Basic Auth:

   ```bash
   curl -i \
     -u "<nickname>:<password>" \
     -X POST http://localhost:8000/api/2/auth/<nickname>/login.json
   ```

5. Confirm the response sets the session cookie.
6. Call the API logout contract using the same cookie:

   ```bash
   curl -i \
     -X POST \
     --cookie "sessionid=<value>" \
     http://localhost:8000/api/2/auth/<nickname>/logout.json
   ```

7. Confirm the logout response succeeds and the session no longer works.

## 5. Verify multilingual behavior

1. Change the language from the account UI.
2. Confirm registration, login, and profile pages render in the selected
   language.
3. Confirm the page document language matches the rendered locale.
4. Confirm an authenticated user's stored language preference wins over a stale
   guest cookie and that the cookie is updated to match.

## 6. Run automated verification

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Run the repository quality and security checks:

   ```bash
   uv run ruff check .
   uv run mypy .
   uv run bandit -r . -c pyproject.toml
   uv run pip-audit
   ```

3. Run the automated test suite:

   ```bash
   uv run pytest -q
   ```

## 7. Prepare for review

1. Ensure commits follow Conventional Commits.
2. Record responsive checks for registration, login, and profile pages.
3. Record API login/logout verification evidence.
4. Open a pull request summarizing delivered account flows, localization checks,
   and any deferred account-management work.
