"""Guards against accidentally committing secrets.

This test scans git-tracked files for patterns that look like real API keys.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import NamedTuple


class SecretPattern(NamedTuple):
    """A pattern to detect a specific type of secret."""

    name: str
    pattern: re.Pattern[str]
    description: str


# AIDEV-NOTE: Secret patterns ordered by specificity (most specific first)
SECRET_PATTERNS = [
    SecretPattern(
        name="Google API Key",
        pattern=re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
        description="Google API keys start with 'AIza'",
    ),
    SecretPattern(
        name="AWS Access Key ID",
        pattern=re.compile(r"AKIA[0-9A-Z]{16}"),
        description="AWS Access Key IDs start with 'AKIA'",
    ),
    SecretPattern(
        name="GitHub Personal Access Token",
        pattern=re.compile(r"ghp_[0-9a-zA-Z]{36}"),
        description="GitHub Personal Access Tokens start with 'ghp_'",
    ),
    SecretPattern(
        name="GitHub OAuth Token",
        pattern=re.compile(r"gho_[0-9a-zA-Z]{36}"),
        description="GitHub OAuth tokens start with 'gho_'",
    ),
    SecretPattern(
        name="GitHub App Token",
        pattern=re.compile(r"(ghu|ghs)_[0-9a-zA-Z]{36}"),
        description="GitHub App tokens start with 'ghu_' or 'ghs_'",
    ),
    SecretPattern(
        name="Private Key",
        pattern=re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY"),
        description="Private key blocks",
    ),
]


def _git_tracked_files(repo_root: Path) -> list[Path]:
    """Return all files tracked by git in the repository."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
    )
    rel_paths = [p for p in result.stdout.splitlines() if p.strip()]
    return [repo_root / p for p in rel_paths]


def _scan_for_secrets(repo_root: Path) -> dict[str, list[str]]:
    """Scan all tracked files for secret patterns.

    Returns a dict mapping secret pattern names to lists of violating file paths.
    """
    violations: dict[str, list[str]] = {}

    for path in _git_tracked_files(repo_root):
        # Skip binary-ish or irrelevant paths.
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pyc"}:
            continue

        # Skip .env.example files - they contain placeholder patterns
        if path.name == ".env.example":
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            continue

        for secret_pattern in SECRET_PATTERNS:
            if secret_pattern.pattern.search(content):
                if secret_pattern.name not in violations:
                    violations[secret_pattern.name] = []
                violations[secret_pattern.name].append(
                    str(path.relative_to(repo_root))
                )

    return violations


def test_no_secrets_committed() -> None:
    """Verify no secrets are committed to git-tracked files."""
    repo_root = Path(__file__).resolve().parents[2]
    violations = _scan_for_secrets(repo_root)

    if violations:
        error_parts = ["Potential secret(s) found in git-tracked files:"]
        for secret_type, files in sorted(violations.items()):
            error_parts.append(f"\n  {secret_type}:")
            for file in sorted(set(files)):
                error_parts.append(f"    - {file}")
        error_parts.append(
            "\n\nRemove the secret(s) and rotate the key(s) if needed."
        )
        raise AssertionError("".join(error_parts))


# AIDEV-NOTE: Keep legacy test name for backwards compatibility with existing CI
def test_no_google_api_keys_committed() -> None:
    """Legacy test name - delegates to comprehensive secret scan."""
    test_no_secrets_committed()
