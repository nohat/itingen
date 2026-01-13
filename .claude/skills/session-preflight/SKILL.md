---
name: session-preflight
description: Session preflight skill. Enforces git/beads/branch checks before any new work.
---

# Session Preflight Skill

This skill enforces mandatory pre-work checks to prevent state-related mistakes (wrong branch, dirty tree, bd sync conflicts).

## When to Use

Run this skill BEFORE:
- Starting any new task
- Switching tasks
- Making any code changes
- Running task-level commands like `bd ready`

## Preflight Checklist (MUST complete in order)

### 1. Git clean state

Run:
```bash
git status --porcelain=v1 -b
```

Rules:
- If there are uncommitted changes, STOP.
- If you are ending a session or switching tasks, run `/land`.

### 2. Branch verification

Rules:
- Confirm you are NOT on `master`.
- Confirm you are on the intended feature branch for the current issue.

### 3. Beads safety check

Rules:
- Feature branches must NEVER include `.beads/issues.jsonl` changes.
- NEVER use `git add -A` or `git add .`.
- Always stage specific directories/files (e.g. `git add src/ tests/ docs/`).
- If `.beads/issues.jsonl` appears modified, run:
```bash
git restore .beads/issues.jsonl
```

### 4. Anchor comments scan

Run:
```bash
grep -r "AIDEV-" src/
```

Rules:
- Read relevant `AIDEV-NOTE`/`AIDEV-TODO`/`AIDEV-QUESTION` anchors before editing related files.
- NEVER delete `AIDEV-NOTE` without explicit human approval.

### 5. Issue tracker state

Run:
```bash
bd list --status in_progress
```

Rules:
- If anything is in-progress and you are about to switch tasks, STOP and run `/land` (or update/close as appropriate).

### 6. Tests (baseline)

Run:
```bash
pytest
```

Rules:
- If tests fail, STOP and fix the implementation (do not change tests to make them pass).

## Required Output

After completing the checklist, output a short summary:
- Branch: <name>
- Git: clean/dirty
- Beads: clean/dirty
- AIDEV scan: completed
- Tests: pass/fail

Do not proceed until this summary is produced.
