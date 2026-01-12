"""Guards against accidentally committing secrets.

This test scans git-tracked files for patterns that look like real API keys.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _git_tracked_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )
    rel_paths = [p for p in result.stdout.splitlines() if p.strip()]
    return [repo_root / p for p in rel_paths]


def test_no_google_api_keys_committed() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    # Google API keys commonly start with "AIza".
    key_pattern = re.compile(r"AIza[0-9A-Za-z\-_]{20,}")

    violations: list[str] = []

    for path in _git_tracked_files(repo_root):
        # Skip binary-ish or irrelevant paths.
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pyc"}:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            continue

        if key_pattern.search(content):
            violations.append(str(path.relative_to(repo_root)))

    assert not violations, (
        "Potential Google API key(s) found in git-tracked files. "
        "Remove the secret(s) and rotate the key(s) if needed. Files: "
        + ", ".join(sorted(violations))
    )
