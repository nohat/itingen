# Trip Itinerary Generator - Claude Code Context

## Engineering Philosophy (Core)

This project optimizes for reliability and maintainability through simplicity and explicitness.

### Simplicity Over Accommodation

- **No speculative fallbacks**: Do not implement recovery paths that are not expected and tested.
- **No legacy compatibility by default**: Avoid carrying forward compatibility logic without a concrete, exercised use case.
- **Fail fast, fail clearly**: Prefer explicit, debuggable errors over best-effort recovery.
- **Delete > Comment out > Keep**: Remove dead code; Git remembers.

### The Fallback Test

Before implementing any fallback, recovery, or compatibility logic, ask:

1. Is this failure case actually expected in production?
2. Will this fallback be regularly exercised and tested?
3. Does the complexity cost justify the theoretical benefit?
4. Would a clear error message be more valuable than silent recovery?

If the answer to any is "no" or "maybe", do not implement the fallback.

### Technical Debt Philosophy

- Code that handles cases that "might happen someday" is technical debt.
- Untested fallback paths are bugs waiting to happen.
- Complexity added for theoretical robustness reduces actual reliability.
- Every branch in the code is a branch that needs testing and maintenance.

## STOP: Session Preflight (MANDATORY)

Before starting any new task, switching tasks, running `bd ready`, or editing code, follow:

**Canonical:** @/.claude/skills/session-preflight/SKILL.md

Hard gates:
- If `git status` is not clean, STOP and run `/land`.
- `.beads/issues.jsonl` should NEVER appear in `git status` (skip-worktree flag must be set).
- Never use `git add -A` or `git add .`.
- Always run `grep -r "AIDEV-" src/` before editing related code.

**Test command:** `pytest`

## Project Overview

A standalone, generic trip itinerary generation system extracted from scaffold project.
This system generates optimized travel itineraries based on venues, constraints, and preferences.

## Non-Negotiables (Operational Rules)

### Git Workflow

- Branch naming: `feat/description`, `fix/description`, `refactor/description`.
- Commit format: `<emoji> <type>(<scope>): <description>`.
- Commit emojis: ✨ feat | 🐛 fix | 📝 docs | ♻️ refactor | ✅ test | 🔧 chore.
- Always commit after each successful test cycle.
- Never commit failing tests (except intentionally in TDD red phase).

### Beads (bd) + Git Integration - CRITICAL

This repo uses **sync-branch mode** where the `bd` daemon commits issue state to a dedicated `beads-sync` branch via a worktree.
The `.beads/issues.jsonl` file is hidden from git status using `--skip-worktree` flags.

#### How Sync-Branch Mode Works

1. **Sync branch**: Issue state is tracked in the `beads-sync` branch (configured in `.beads/config.yaml`).
2. **Worktree isolation**: `.git/beads-worktrees/beads-sync/` is a separate checkout for daemon commits.
3. **Skip-worktree flags**: `.beads/issues.jsonl` has `git update-index --skip-worktree` set on all branches.
4. **Daemon auto-syncs**: Creates "bd daemon sync" commits on `beads-sync` automatically.
5. **Config is tracked**: `.beads/config.yaml` IS tracked in git and can be committed to feature branches.

#### Critical Rules

- ❌ **NEVER** `git add .beads/issues.jsonl` - it should be invisible to git status.
- ❌ **NEVER** `git add -A` or `git add .` - always stage specific paths.
- ❌ **NEVER** `git update-index --no-skip-worktree .beads/issues.jsonl` - this breaks sync-branch mode.
- ✅ **ALWAYS** stage specific paths: `git add src/ tests/ docs/`.
- ✅ **OK to commit** `.beads/config.yaml` if you change sync-branch settings.
- ✅ **ALWAYS** let `bd sync` handle issue state - it syncs to `beads-sync` branch automatically.

#### Correct Feature Branch Workflow

```bash
# Start feature (from clean master)
git checkout -b feat/my-feature origin/master
bd update <issue-id> --status in_progress

# Verify .beads/issues.jsonl is NOT in git status (skip-worktree working)
git status  # Should show clean or only code changes

# Commit ONLY code (stage specific paths)
git add src/ tests/ docs/
git commit -m "✨ feat: my feature"

# End session
bd close <issue-id>
bd sync                         # Commits to beads-sync via worktree - NOT your branch
git push origin feat/my-feature # Push feature branch only
```

#### Recovery: If .beads/issues.jsonl Appears in Git Status

If `.beads/issues.jsonl` shows as modified in `git status`, the skip-worktree flag is missing:

```bash
# Fix: Set skip-worktree flag
git update-index --skip-worktree .beads/issues.jsonl
git status  # Should now be clean

# If still showing changes, restore to HEAD first
git update-index --no-skip-worktree .beads/issues.jsonl
git restore .beads/issues.jsonl
git update-index --skip-worktree .beads/issues.jsonl
```

#### Recovery: Fix All Local Branches

If you need to set skip-worktree on all local branches:

```bash
# Visit each branch and set the flag
for branch in $(git branch --format='%(refname:short)' | grep -v '^beads-sync$'); do
  git checkout -f "$branch"
  git update-index --skip-worktree .beads/issues.jsonl
done
git checkout -  # Return to previous branch
```

### Anchors (AIDEV-*)

- Always scan anchors before editing: `grep -r "AIDEV-" src/`.
- Update relevant anchors when modifying associated code.
- Never delete `AIDEV-NOTE` without explicit human approval.

### Specs

- Match implementation to `docs/ARCHITECTURE.md`, `requirements.txt`, and `pyproject.toml`.

### Test-Driven Development (TDD) - MANDATORY

**Canonical:** @/.claude/skills/tdd/SKILL.md

## How Work Proceeds Here (Workflow)

### Start-of-Session / Handoff

- Prefer `/start` for a full guided start.
- **Canonical skill:** @/.claude/skills/handoff-start/SKILL.md

### Issue Tracking (Beads)

Quick reference:

```bash
bd ready
bd show <id>
bd update <id> --status in_progress
bd close <id>
bd sync
```

#### Before Starting ANY New Task - MANDATORY CHECK

Always execute these checks before starting new work:

1. Check git status. If uncommitted changes exist, execute `/land` first.
2. Check issue tracker. If tasks are in progress, update or land them first.
3. Verify clean state. Only proceed with new work when everything is properly landed.

### Ending a Session (MANDATORY)

Always run `/land` before ending work. Work is not complete until the full protocol is finished.

**Canonical:** @/.claude/commands/land.md

#### Work Continuation Rules

- Never start new tasks without first landing current work.
- Never switch tasks without completing the land protocol.
- Never respond to new requests when work is in-progress and uncommitted.
- Never continue work after user says "done", "stop", or "pause" without landing.

#### Push to Remote (MANDATORY)

```bash
git pull --rebase
bd sync
git push
git status  # MUST show "up to date with origin"
```

**MANDATORY WORKFLOW:**
1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Create PR to master** - If not on `master` and no PR exists for the branch:
   ```bash
   gh pr create --base master --fill
   ```
6. **Clean up** - Clear stashes, prune remote branches
7. **Verify** - All changes committed AND pushed
8. **Hand off** - Provide context for next session

## Slash Commands (preferred)

- `/start`: @/.claude/commands/start.md
- `/plan`: @/.claude/commands/plan.md
- `/test`: @/.claude/commands/test.md
- `/review`: @/.claude/commands/review.md
- `/commit`: @/.claude/commands/commit.md
- `/land`: @/.claude/commands/land.md

## What AI Must NEVER Do

1. Skip the TDD cycle.
2. Write large amounts of code without tests.
3. Modify test assertions to make them pass.
4. Remove anchor comments without permission.
5. Commit directly to `master`.
6. Make breaking changes without updating docs.
7. Ignore failing tests.
8. Over-engineer solutions beyond stated requirements.
9. Implement speculative fallbacks or "just in case" error handling.
10. Add backwards compatibility logic without a concrete, exercised use case.
11. Blindly adopt inherited patterns without critical evaluation.
12. Start new tasks without landing previous work first.
13. Switch tasks without completing land protocol.
14. Leave uncommitted changes when responding to new requests.
15. Continue work after user says "done", "stop", or "pause" without landing.
16. Implement with libraries not specified in `requirements.txt`/`pyproject.toml`.
17. Deviate from `docs/ARCHITECTURE.md` without explicit approval.
18. Remove skip-worktree flag from `.beads/issues.jsonl` (breaks sync-branch mode).
19. Use `git add -A` or `git add .` (risks staging unintended files).
20. Commit `.beads/issues.jsonl` to feature branches (should be invisible to git).

## Domain Glossary

- **Venue**: A location that can be visited (restaurant, attraction, etc.).
- **Itinerary**: An ordered schedule of venue visits with timing.
- **Constraint**: A rule that limits itinerary options (hours, distance, etc.).
- **Slot**: A time block in the itinerary.

## Inherited Technical Decisions

See `docs/INHERITED_DECISIONS.md` for architectural patterns and conventions reviewed from the original scaffold project.

Inherited decisions are a starting point, not gospel. Critically evaluate each decision against the needs of this project.

## Anchor Comments System

Use these prefixed comments throughout the codebase:

- `AIDEV-NOTE:` - Important context for AI and developers (≤120 chars)
- `AIDEV-TODO:` - Work items that need attention
- `AIDEV-QUESTION:` - Uncertainties that need human clarification
- `AIDEV-DECISION:` - Records of architectural decisions made

Before scanning files, always grep for `AIDEV-*` first to understand context.

## Issue Tracking CLI

- `bd create "Task" -p 1` - Create issue
- `bd ready` - Find unblocked work
- `bd close <id>` - Complete work
- `bd dep add <child> <parent>` - Track dependencies

File discovered work as you go. At session end, run `bd sync`.

## Commands Reference

- `pytest` - Run all tests
- `ruff check .` - Run linter

- `[PACKAGE_MANAGER] run build` - Build the project
- `[PACKAGE_MANAGER] run test` - Run all tests
- `[PACKAGE_MANAGER] run test:watch` - Run tests in watch mode
- `[PACKAGE_MANAGER] run lint` - Run linter
- `[PACKAGE_MANAGER] run typecheck` - Run type checker

## Code Style

- [TO BE DETERMINED based on source analysis]

## Architecture Patterns

- [TO BE DETERMINED based on source analysis]

## Issue Tracking

Use `bd` for all task tracking instead of markdown TODO lists.

## Canonical References

- Skills router: `@/.windsurf/rules/skills-router.md`
- Skills index (generated): `@/.windsurf/rules/skills-index.generated.md`
- Workflow router: `@/.windsurf/rules/workflow-router.md`
- Architecture: `@/docs/ARCHITECTURE.md`
