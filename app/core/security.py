from __future__ import annotations

import binascii
import hashlib
import hmac
import re
import secrets
from urllib.parse import urlsplit, urlunsplit

NICKNAME_RE = re.compile(r"^[A-Za-z0-9_-]{8,16}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEVICE_ID_RE = re.compile(r"^[\w.-]+$")
JSONP_CALLBACK_RE = re.compile(r"^[A-Za-z_$][\w.$]*$")

SUBSCRIPTION_FORMATS = ("json", "opml", "txt")
EPISODE_ACTION_TYPES = ("download", "delete", "play", "new", "flattr")

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 600_000
PBKDF2_SALT_BYTES = 16


def validate_secret_key(secret_key: str) -> None:
    if len(secret_key) < 32:
        raise ValueError("secret_key must contain at least 32 characters")


def validate_nickname(nickname: str) -> str:
    cleaned = nickname.strip()
    if not NICKNAME_RE.fullmatch(cleaned):
        raise ValueError(
            "nickname must contain 8 to 16 letters, numbers, underscores, or hyphens"
        )
    return cleaned


def validate_email_address(email: str) -> str:
    cleaned = email.strip().lower()
    if not EMAIL_RE.fullmatch(cleaned):
        raise ValueError("email must be valid")
    return cleaned


def validate_device_id(device_id: str) -> str:
    cleaned = device_id.strip()
    if not cleaned or not DEVICE_ID_RE.fullmatch(cleaned):
        raise ValueError("device_id must match [\\w.-]+")
    if len(cleaned) > 255:
        raise ValueError("device_id must not exceed 255 characters")
    return cleaned


def validate_since_timestamp(value: int | None) -> int | None:
    if value is None:
        return None
    if value < 0:
        raise ValueError("since must be greater than or equal to zero")
    return value


def validate_subscription_format(value: str) -> str:
    cleaned = value.strip().lower()
    if cleaned not in SUBSCRIPTION_FORMATS:
        raise ValueError("format must be one of json, opml, txt")
    return cleaned


def validate_jsonp_callback(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("jsonp callback must not be empty")
    if not JSONP_CALLBACK_RE.fullmatch(cleaned):
        raise ValueError("jsonp callback contains invalid characters")
    return cleaned


def sanitize_subscription_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"}:
        return ""
    return cleaned


def sanitize_episode_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    try:
        cleaned.encode("ascii")
    except UnicodeEncodeError:
        return ""
    parsed = urlsplit(cleaned)
    if parsed.scheme.lower() not in {"http", "https"}:
        return ""
    return cleaned


def validate_episode_action(value: str) -> str:
    cleaned = value.strip().lower()
    if cleaned not in EPISODE_ACTION_TYPES:
        raise ValueError("action must be one of download, delete, play, new, flattr")
    return cleaned


def validate_episode_query_url(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    sanitized = sanitize_episode_url(value)
    if not sanitized:
        raise ValueError(f"{field_name} must be an ASCII http or https URL")
    return sanitized


def validate_episode_progress(
    *,
    action: str,
    started: int | None,
    position: int | None,
    total: int | None,
) -> tuple[int | None, int | None, int | None]:
    values = (started, position, total)
    if action == "play":
        if any(value is None for value in values):
            raise ValueError(
                "play actions require started, position, and total together"
            )
        return values
    if any(value is not None for value in values):
        raise ValueError("started, position, and total are only valid for play")
    return values


def derive_password_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        binascii.hexlify(derived).decode("ascii"),
        binascii.hexlify(salt).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    derived = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        binascii.unhexlify(stored_salt.encode("ascii")),
        PBKDF2_ITERATIONS,
    )
    expected = binascii.hexlify(derived).decode("ascii")
    return hmac.compare_digest(expected, stored_hash)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


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
