#!/usr/bin/env bash
# Secret scanning pre-commit hook
# This script runs the secret scanning test to prevent accidentally committing secrets.
#
# To install as a git hook:
#   ln -sf ../../scripts/check_secrets.sh .git/hooks/pre-commit-secrets
#
# Or add to your existing pre-commit hook:
#   ./scripts/check_secrets.sh || exit 1

set -euo pipefail

# Change to repo root
cd "$(git rev-parse --show-toplevel)"

echo "🔍 Scanning for committed secrets..."

# Run the secret scanning test
if python -m pytest tests/unit/test_no_secrets_committed.py -q; then
    echo "✅ No secrets detected"
    exit 0
else
    echo "❌ Secret scanning failed - review the output above"
    echo "   Remove any secrets and rotate compromised keys before committing"
    exit 1
fi
