from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.check_conventional_commit import main

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_conventional_commit_validator_accepts_valid_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = tmp_path / "commit.txt"
    message.write_text("feat(api): add readiness endpoint\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_conventional_commit.py", str(message)])
    assert main() == 0


def test_conventional_commit_validator_rejects_invalid_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = tmp_path / "commit.txt"
    message.write_text("update stuff\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_conventional_commit.py", str(message)])
    assert main() == 1
