from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def validate_secret_key(secret_key: str) -> None:
    if len(secret_key) < 32:
        raise ValueError("secret_key must contain at least 32 characters")


def redact_database_url(url: str) -> str:
    parts = urlsplit(url)
    if "@" not in parts.netloc:
        return url
    credentials, host = parts.netloc.rsplit("@", 1)
    username = credentials.split(":", 1)[0]
    redacted_netloc = f"{username}:***@{host}"
    return urlunsplit(
        (parts.scheme, redacted_netloc, parts.path, parts.query, parts.fragment)
    )
