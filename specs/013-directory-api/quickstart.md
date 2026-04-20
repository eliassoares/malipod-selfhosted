# Quickstart: Directory API

**Date**: 2026-04-20
**Spec**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/013-directory-api/spec.md`

## Run locally

1) Start the app:

- `make run`

2) Ensure the server has at least one subscribed podcast in its local catalog
   (via existing subscription/device flows or by seeding in dev DB).

## Manual checks

- Search JSON:
  - `curl -s 'http://localhost:8000/search.json?q=linux' | jq .`
- Search OPML:
  - `curl -s 'http://localhost:8000/search.opml?q=linux' | head`
- Toplist TXT:
  - `curl -s 'http://localhost:8000/toplist/10.txt'`
- Tags:
  - `curl -s 'http://localhost:8000/api/2/tags/10.json' | jq .`
- Podcast data:
  - `curl -s 'http://localhost:8000/api/2/data/podcast.json?url=https%3A%2F%2Fexample.com%2Ffeed.xml' | jq .`
