<!--
Sync Impact Report
- Version change: 1.1.0 -> 1.2.0
- Modified principles:
  - I. Spec-First Delivery -> I. Spec-First Delivery
  - III. Verification Before Merge -> III. Verification Before Merge
  - IV. Strict Python Quality Gates -> IV. Strict Python Quality Gates
- Added sections:
  - None
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
- Follow-up TODOs:
  - None
-->
# Malipod Constitution

## Core Principles

### I. Spec-First Delivery
Every material change MUST start with a specification, plan, and task breakdown
under `specs/` before implementation begins. Specs MUST state user value,
requirements, measurable success criteria, edge cases, and explicit assumptions so
delivery decisions can be audited after the fact.

Each feature MUST be implemented on a dedicated branch created from `main`.
Direct feature work on `main` is not allowed.

Rationale: the repository is configured around Spec Kit workflows; bypassing that
structure would break planning traceability and reduce decision quality.

### II. Independently Valuable Slices
Work MUST be organized as independently testable user stories ordered by priority.
The first slice MUST produce a usable MVP on its own, and later slices MUST add
value without making earlier slices dependent on unfinished work.

Rationale: incremental delivery reduces risk and keeps the codebase demonstrable at
every checkpoint.

### III. Verification Before Merge
Behavior changes MUST ship with verification proportional to risk. At minimum, any
change affecting runtime behavior, data handling, or interfaces MUST define how it
will be validated and MUST execute the relevant automated checks before merge.
When tests are added, they MUST fail before implementation and pass afterward.
Once implementation and verification are complete, the contributor MUST open a
pull request before the work is considered ready to merge.

Rationale: quality is enforced by evidence, not intent; explicit verification keeps
changes reviewable and repeatable.

### IV. Strict Python Quality Gates
Production code MUST remain compatible with Python 3.13 and pass the repository's
quality gates: Ruff, MyPy strict mode, Bandit, and dependency audit where
applicable. New code MUST include precise typing, small focused modules, and clear
interfaces that match the actual project structure under `app/` and `tests/`.
Suppressing tool output with `# noqa`, `# nosec`, or equivalent inline waivers is
not allowed as a convenience shortcut. Contributors MUST first try to fix the
underlying typing, lint, or security issue directly. An exception is acceptable
only when the rule is demonstrably incorrect for the specific code path and the
justification is documented in the plan's Complexity Tracking section and called
out during review.

Rationale: this repository is already wired for strict static analysis and security
tooling, so the constitution makes those checks non-optional.

### V. Security and Simplicity by Default
Designs MUST prefer the simplest approach that satisfies the current spec. New
dependencies, architectural layers, and persistence choices MUST be justified in
the plan. Inputs, secrets, and external integrations MUST be treated as hostile by
default, with validation and least-privilege handling documented in the work.

Rationale: early-stage projects move faster when complexity and security exposure
are both deliberate rather than accidental.

## Engineering Standards

- Runtime code belongs under `app/`; tests belong under `tests/`; feature planning
  artifacts belong under `specs/<feature>/`.
- Plans MUST document language version, dependencies, storage, testing approach,
  constraints, and structure decisions using the real repository layout.
- Specifications MUST capture functional requirements, edge cases, assumptions, and
  measurable outcomes in technology-agnostic terms.
- Tasks MUST include concrete file paths, identify parallel-safe work accurately,
  and reserve cross-cutting work for the final polish phase unless it blocks
  delivery earlier.

## Workflow and Review Gates

- The implementation plan MUST pass a Constitution Check before research or design
  continues.
- Feature branches MUST be created from `main`, remain focused on a single
  feature, and be merged back only through a pull request.
- All commits on feature branches MUST follow the Conventional Commits
  specification, such as `feat:`, `fix:`, `docs:`, `refactor:`, or `test:`.
- Code review MUST reject changes that lack spec traceability, verification
  evidence, or justification for added complexity.
- Code review MUST reject changes that silence Ruff, MyPy, or Bandit findings
  with inline waivers unless the waiver is explicitly justified, documented, and
  reviewed as an exception.
- Before merge, contributors MUST run the relevant local checks from the current
  change set, which normally includes `uv run ruff check .`, `uv run mypy .`,
  `uv run bandit -r . -c pyproject.toml`, and feature-specific tests.
- Every pull request MUST summarize the implemented scope, the verification that
  was executed, and any follow-up work intentionally left out of the branch.
- Exceptions are allowed only when documented in the plan's Complexity Tracking
  section with the reason, the rejected simpler alternative, and the remediation
  path.

## Governance

This constitution overrides conflicting local habits and informal process notes for
this repository. Amendments require an explicit update to this file, a summary of
affected principles or sections, and synchronized updates to any templates that
enforce the changed rules.

Versioning policy follows semantic versioning for governance:
- MAJOR for removed or fundamentally redefined principles.
- MINOR for new principles, sections, or materially expanded requirements.
- PATCH for clarifications that do not change expected behavior.

Compliance review is mandatory during planning and review. Every implementation
plan MUST document constitution gates, and every pull request or equivalent review
MUST confirm those gates were satisfied or explicitly waived with justification.

**Version**: 1.2.0 | **Ratified**: 2026-04-08 | **Last Amended**: 2026-04-15
