from __future__ import annotations

import hashlib
import secrets

PLACEHOLDER_FILENAMES = ("lilith.png", "malte.png")
PLACEHOLDER_URLS = tuple(
    f"/static/placeholders/{name}" for name in PLACEHOLDER_FILENAMES
)


def choose_placeholder_url_random() -> str:
    return secrets.choice(PLACEHOLDER_URLS)


def choose_placeholder_url_stable(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    index = int.from_bytes(digest[:2], "big") % len(PLACEHOLDER_URLS)
    return PLACEHOLDER_URLS[index]
