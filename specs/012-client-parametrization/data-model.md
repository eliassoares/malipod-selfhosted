# Data Model: Client Parametrization

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/spec.md`

This feature does not introduce database entities or persistence.

## Contract Entities (Response Documents)

### ClientConfigResponse

- **Represents**: The JSON document returned by `GET /clientconfig.json`.
- **Fields**:
  - `mygpo` (object)
    - `baseurl` (string): server base URL, normalized to end with `/`.
  - `mygpo-feedservice` (object)
    - `baseurl` (string): same value as `mygpo.baseurl` (compatibility).
  - `update_timeout` (integer): seconds clients may cache this configuration.
- **Validation rules**:
  - `update_timeout` must be a positive integer.
  - `mygpo.baseurl` must be a non-empty string.
  - `mygpo.baseurl` must end with `/` after normalization.

## Derived Values

- `baseurl`: derived from the server’s existing configured base URL.
- `update_timeout`: fixed constant (per spec assumptions; no new configuration).
