from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_TYPES = (
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
)

CONVENTIONAL_RE = re.compile(
    r"^(?:fixup!\s|squash!\s)?"
    r"(?P<type>" + "|".join(ALLOWED_TYPES) + r")"
    r"(?:\([a-z0-9][a-z0-9._/-]*\))?"
    r"!?:"
    r" .+$"
)

ALLOWED_SPECIAL_PREFIXES = ("Merge ", "Revert ")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_conventional_commit.py <commit-msg-file>", file=sys.stderr)
        return 2

    message_path = Path(sys.argv[1])
    lines = message_path.read_text(encoding="utf-8").splitlines()
    subject = next(
        (line.strip() for line in lines if line.strip() and not line.startswith("#")),
        "",
    )

    if not subject:
        print("empty commit message is not allowed", file=sys.stderr)
        return 1

    if subject.startswith(ALLOWED_SPECIAL_PREFIXES):
        return 0

    if CONVENTIONAL_RE.match(subject):
        return 0

    allowed = ", ".join(ALLOWED_TYPES)
    print("commit message must follow Conventional Commits", file=sys.stderr)
    print(f"allowed types: {allowed}", file=sys.stderr)
    print("example: feat(auth): add user login endpoint", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
