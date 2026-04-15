# Data Model: Podcast Sync Platform Foundation

## Overview

This phase defines the minimum operational entities needed to run the product
foundation safely. The model is intentionally small and focuses on startup,
configuration, readiness, and future extensibility rather than full sync-domain
behavior.

## Entity: RuntimeConfiguration

**Purpose**: Represents the validated runtime settings required for the platform
to start and operate safely.

**Fields**:
- `environment`: deployment mode identifier
- `app_name`: display name used by the site and API
- `database_url`: primary runtime storage connection
- `secret_key`: application secret used for session and security operations
- `allowed_hosts`: trusted host list
- `log_level`: runtime logging level

**Validation Rules**:
- `database_url` must be present and parseable
- `secret_key` must meet minimum entropy/length requirements
- `environment` must map to an approved runtime mode
- `allowed_hosts` must not be empty outside explicit local-development mode

**Relationships**:
- Governs application startup
- Supplies inputs to `ApplicationSurface` and `ReadinessProbe`

## Entity: ApplicationSurface

**Purpose**: Represents one externally visible product surface exposed by the
foundation.

**Fields**:
- `surface_name`: stable identifier such as `site` or `api`
- `surface_type`: browser-facing or machine-facing
- `route_prefix`: externally reachable entry path
- `status`: current availability state

**Validation Rules**:
- `surface_name` must be unique
- `route_prefix` must be routable and non-empty
- `status` must be one of `starting`, `ready`, or `degraded`

**Relationships**:
- Linked to one or more `ReadinessProbe` checks

## Entity: ReadinessProbe

**Purpose**: Captures the checks used to decide whether the platform is ready to
accept normal traffic.

**Fields**:
- `probe_name`: unique readiness check name
- `target_surface`: related application surface
- `check_result`: latest pass/fail state
- `failure_reason`: actionable explanation when not ready
- `checked_at`: timestamp of last evaluation

**Validation Rules**:
- `probe_name` must be unique
- `check_result` must be boolean or mapped ready/not-ready state
- `failure_reason` is required when `check_result` is false

**Relationships**:
- Belongs to `ApplicationSurface`
- Depends on `RuntimeConfiguration`

## Entity: DataContext

**Purpose**: Distinguishes storage usage between development/runtime and
automated verification.

**Fields**:
- `context_name`: logical name of the storage context
- `context_type`: runtime or test
- `driver_family`: storage driver class
- `is_isolated`: whether writes must be isolated from normal development state

**Validation Rules**:
- `context_name` must be unique within the environment
- `context_type` must be one of `runtime` or `test`
- `is_isolated` must be true for test contexts

**Relationships**:
- Used by `RuntimeConfiguration`
- Evaluated by `ReadinessProbe` for verification workflows

## Entity: ReviewArtifact

**Purpose**: Represents the structured review summary required before merge.

**Fields**:
- `change_scope`: concise summary of what the branch delivers
- `verification_summary`: list of checks and results
- `follow_up_items`: deferred work items
- `branch_name`: source branch under review

**Validation Rules**:
- `change_scope` must not be empty
- `verification_summary` must include at least one executed validation item
- `branch_name` must match the active feature branch

**Relationships**:
- Produced from implementation work on the feature branch
- Consumed during PR review

## Future Domain Extension Notes

This foundation is intentionally designed to grow into later entities such as
`User`, `PodcastSubscription`, `PodcastFeed`, `Episode`, and `SyncEvent` without
requiring a structural rewrite of the project layout.
