# Research: Podcast Sync Platform Foundation

## Decision: Use a single FastAPI application for both API and site delivery

**Rationale**: The first increment needs a browser-visible site and an HTTP API
without introducing coordination overhead between separate services. A single
FastAPI application supports JSON endpoints and server-rendered pages with one
runtime, one configuration model, and one security boundary, which fits the
constitution's simplicity requirement.

**Alternatives considered**:
- Separate backend and frontend services: clearer isolation later, but too much
  infrastructure for the foundation phase.
- API-only service with no initial site: simpler technically, but fails the
  feature spec's requirement for both product surfaces.

## Decision: Follow a layered FastAPI project structure inside `app/`

**Rationale**: The referenced best-practice material consistently favors
separating routing, configuration, database access, schemas, and business logic.
Using `api/`, `core/`, `db/`, `schemas/`, `services/`, and `templates/` keeps
the codebase easy to navigate while avoiding premature microservice splits.

**Alternatives considered**:
- Flat module layout: faster for a toy app, but harder to scale into user,
  subscription, and episode sync features.
- Domain-heavy architecture from day one: potentially cleaner long term, but too
  much ceremony for the initial foundation.

## Decision: Run the app with Docker Compose and PostgreSQL for development

**Rationale**: The user explicitly wants Docker and Docker Compose, plus
PostgreSQL as the main database. Compose provides a consistent local startup
path, while PostgreSQL matches the likely future sync workload better than an
embedded database for day-to-day development.

**Alternatives considered**:
- Local process startup without containers: lighter weight, but less consistent
  across contributors and less aligned with the requested workflow.
- SQLite for all environments: simpler, but not representative enough for the
  target runtime data model.

## Decision: Use SQLAlchemy 2.x with `asyncpg` for PostgreSQL access

**Rationale**: This keeps the foundation aligned with FastAPI's async request
model, works well with a layered application structure, and avoids carrying two
database access patterns from the start.

**Alternatives considered**:
- `psycopg` 3 async support: viable, but `asyncpg` remains the more common fit
  for SQLAlchemy async foundations.
- Synchronous database access only: simpler initially, but less aligned with the
  chosen application model.

## Decision: Use SQLite only for automated tests

**Rationale**: The feature spec requires isolated verification that does not
touch development data. SQLite enables fast, disposable test runs and keeps the
test workflow independent from a running PostgreSQL instance when appropriate.

**Alternatives considered**:
- PostgreSQL for every test: highest fidelity, but slower and heavier for the
  initial project foundation.
- Shared test database: easier to wire once, but violates the requirement for
  isolated verification.

## Decision: Enforce pinned dependencies and repository-level security checks

**Rationale**: The user explicitly requires pinned versions and a security focus.
The existing repository already includes Ruff, MyPy, Bandit, pip-audit, and
pre-commit; the foundation should formalize those as part of the standard local
verification and review flow.

**Alternatives considered**:
- Floating dependency ranges only: easier upgrades, but weaker reproducibility.
- Security checks only in CI: useful later, but insufficient as the primary
  guardrail for local developer workflows.

## Decision: Validate configuration at startup and expose liveness/readiness endpoints

**Rationale**: The spec requires safe startup failure and independent validation
of product surfaces. Up-front configuration validation reduces accidental unsafe
states, and separate liveness/readiness endpoints give clear operational signals
for both local development and future deployment environments.

**Alternatives considered**:
- Lazy validation on first request: less code at startup, but failures surface
  later and are harder to diagnose.
- Single generic health endpoint: simpler, but weaker signal for readiness vs.
  process availability.

## Decision: Use server-rendered HTML for the initial site surface

**Rationale**: The site surface in this phase only needs to demonstrate product
availability and readiness. Server-rendered templates keep the implementation
small, work naturally inside a single FastAPI app, and avoid adding a frontend
build chain before the product needs one.

**Alternatives considered**:
- Separate SPA frontend: powerful later, but unnecessary complexity right now.
- Static HTML only: smallest option, but less flexible for future authenticated
  dashboard flows.
