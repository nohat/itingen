#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"

echo "[sync_windsurf] repo_root=${repo_root}"

skills_index_script="${repo_root}/scripts/skills_index_generate.py"
workflows_sync_script="${repo_root}/scripts/commands_workflows_sync.py"
workflow_router="${repo_root}/.windsurf/rules/workflow-router.md"

if [[ ! -f "${skills_index_script}" ]]; then
  echo "[sync_windsurf] ERROR: missing ${skills_index_script}" >&2
  exit 1
fi

if [[ ! -f "${workflows_sync_script}" ]]; then
  echo "[sync_windsurf] ERROR: missing ${workflows_sync_script}" >&2
  exit 1
fi

echo "[sync_windsurf] Regenerating skills index..."
python "${skills_index_script}"

echo "[sync_windsurf] Generating workflow wrappers from .claude/commands..."
python "${workflows_sync_script}"

echo "[sync_windsurf] Updating workflow router..."
mkdir -p "$(dirname "${workflow_router}")"

cat > "${workflow_router}" <<'EOF'
# Workflow Router

This rule routes Windsurf slash commands to their canonical definitions in `.claude/commands/`.

## Available Workflows

- **/start**: Start-of-session protocol. See `.windsurf/workflows/start.md`.
- **/land**: Session end protocol. See `.windsurf/workflows/land.md`.
- **/commit**: Git commit protocol. See `.windsurf/workflows/commit.md`.
- **/plan**: Work planning protocol. See `.windsurf/workflows/plan.md`.
- **/test**: Testing protocol. See `.windsurf/workflows/test.md`.
- **/review**: Code review protocol. See `.windsurf/workflows/review.md`.

## Instructions

When a user uses a slash command, consult the corresponding workflow file in `.windsurf/workflows/` or the command file in `.claude/commands/` and follow its instructions exactly.
EOF

echo "[sync_windsurf] Done."
echo "[sync_windsurf] Changed files (if any):"
git -C "${repo_root}" status --porcelain=v1 .windsurf || true
