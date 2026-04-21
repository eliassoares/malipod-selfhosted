from __future__ import annotations

import http.client
import json
import re

_APPLE_ID_RE = re.compile(r"podcasts\.apple\.com/.*/id(\d+)", re.IGNORECASE)


def resolve_apple_podcasts_url(url: str) -> str | None:
    """Return the RSS feed URL for an Apple Podcasts URL, or None if not resolvable."""
    match = _APPLE_ID_RE.search(url)
    if not match:
        return None
    podcast_id = match.group(1)
    conn = http.client.HTTPSConnection("itunes.apple.com", timeout=10)
    try:
        conn.request(
            "GET",
            f"/lookup?id={podcast_id}&entity=podcast",
            headers={"User-Agent": "malipod/0.1", "Accept": "application/json"},
        )
        response = conn.getresponse()
        if response.status != 200:
            return None
        raw = response.read(1 * 1024 * 1024)
    except (OSError, http.client.HTTPException):
        return None
    finally:
        conn.close()
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return None
    results = data.get("results") or []
    if not results:
        return None
    return results[0].get("feedUrl") or None
