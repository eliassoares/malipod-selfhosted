# Quickstart: Client Parametrization

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/012-client-parametrization/spec.md`

## Run locally

1) Configure environment (example):

- `BASE_URL=http://localhost:8000`

2) Start the server:

- `make run`

## Verify manually

- `curl -s http://localhost:8000/clientconfig.json | jq .`

Expected shape:

- `.mygpo.baseurl` ends with `/`
- `.update_timeout` is a positive integer
