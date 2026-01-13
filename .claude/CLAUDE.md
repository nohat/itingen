# Trip Itinerary Generator - Claude Code Context

## STOP: Session Preflight (MANDATORY)

Before starting any new task, switching tasks, running `bd ready`, or editing code, follow:

**Canonical:** @/Users/nohat/play/itingen/.claude/skills/session-preflight/SKILL.md

Hard gates:
- If `git status` is not clean, STOP and run `/land`.
- Never commit `.beads/issues.jsonl` on a feature branch.
- Never use `git add -A` or `git add .`.
- Always run `grep -r "AIDEV-" src/` before editing related code.

**Test command:** `pytest`

## Project Overview
A standalone, generic trip itinerary generation system extracted from scaffold project.
This system generates optimized travel itineraries based on venues, constraints, and preferences.

## How Work Proceeds Here

### TDD (MANDATORY)

**Canonical:** @/Users/nohat/play/itingen/.claude/skills/tdd/SKILL.md

### Git Workflow & Branching
- **Main Branch**: `master` is the source of truth. **NEVER** commit directly to `master`.
- **Feature Branches**: Every task MUST start with a new feature branch.
  - Format: `feat/description`, `fix/description`, `refactor/description`.
  - Example: `git checkout -b feat/pdf-export`.
- **Worktrees**: Use `bd worktree create <name>` for parallel development or isolation.
  - **Preferred Workflow**: `bd worktree create feat-branch-name --branch feat/branch-name`.
  - Avoid working directly in the repository root if multiple tasks are active.
  - See `docs/agent-workspaces.md` for the standard on isolated worktrees.
- **Commit format**: `<emoji> <type>(<scope>): <description>`
- **Commit emojis**: ✨ feat | 🐛 fix | 📝 docs | ♻️ refactor | ✅ test | 🔧 chore
- **Atomic Commits**: Each commit should represent one logical change.
- **Verification**: ALWAYS run tests before committing.
- **Syncing**: ALWAYS run `bd sync` and `git push` after committing to ensure remote and tracker are updated.

### Start-of-Session / Handoff

**Canonical:** @/Users/nohat/play/itingen/.claude/skills/handoff-start/SKILL.md

### Slash Commands (preferred)

- `/plan`: @/Users/nohat/play/itingen/.claude/commands/plan.md
- `/test`: @/Users/nohat/play/itingen/.claude/commands/test.md
- `/commit`: @/Users/nohat/play/itingen/.claude/commands/commit.md
- `/land`: @/Users/nohat/play/itingen/.claude/commands/land.md

## Non-Negotiables

### Git & Beads

- Feature branches must NEVER include `.beads/issues.jsonl` changes.
- Do not use `git add -A` or `git add .`.
- If `.beads/issues.jsonl` appears modified on a feature branch: `git restore .beads/issues.jsonl`.

### Anchors

- Always scan anchors before editing: `grep -r "AIDEV-" src/`.
- Never delete `AIDEV-NOTE` without explicit human approval.

### Specs

- Match implementation to `docs/ARCHITECTURE.md`, `requirements.txt`, and `pyproject.toml`.

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

## Canonical References

- Skills router: `@/Users/nohat/play/itingen/.windsurf/rules/skills-router.md`
- Skills index (generated): `@/Users/nohat/play/itingen/.windsurf/rules/skills-index.generated.md`
- Workflow router: `@/Users/nohat/play/itingen/.windsurf/rules/workflow-router.md`
- Architecture: `@/Users/nohat/play/itingen/docs/ARCHITECTURE.md`
