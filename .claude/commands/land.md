---
description: Land the plane - session end protocol (capture work, commit, sync tracker)
allowed-tools: Bash(git:*), Bash(bd:*), Bash(gh:*), Bash(npm:*), Bash(python:*), Read, Glob, Grep
---

# Land the Plane - Session End Protocol

## Usage
```
/land
```

## CRITICAL: AI Assistant Behavior - PREVENT WORK CONTINUATION

**MANDATORY LANDING BEFORE NEW WORK**: The AI assistant MUST execute this protocol BEFORE:
- Starting any new task or issue
- Switching between different tasks
- Responding to new user requests after completing work
- Ending any session or conversation

**WORK CONTINUATION BLOCKERS**: The AI assistant is FORBIDDEN from:
1. ❌ Starting new tasks without first landing current work
2. ❌ Switching tasks without completing the land protocol
3. ❌ Responding to new requests when work is in-progress and uncommitted
4. ❌ Continuing work after user says "done", "stop", "pause", etc. without landing

**MANDATORY CHECKPOINTS**: Before ANY new work, AI assistant MUST:
1. Check git status - if uncommitted changes exist, execute `/land` first
2. Check issue tracker status - if tasks in-progress, update or land them first  
3. Verify all previous work is properly committed and synced

**ONLY AFTER** all work is landed may the assistant proceed with new tasks.

## Process (execute in order)

### 1. Capture Discovered Work
- Review any TODOs, FIXMEs, or issues discovered during this session
- File them as Beads issues: `bd create "description" -p <priority> -t <type>`
- Link discovered work to parent tasks: `bd dep add <new> <parent> --type discovered-from`

### 2. Update Existing Issues
- Close completed issues: `bd close <id> --reason "description"`
- Update in-progress issues with current status
- Adjust priorities if understanding has changed

### 3. Record Learnings
- Update AIDEV-NOTE comments for any non-obvious code written
- Add AIDEV-DECISION comments for architectural choices made
- Update docs/ARCHITECTURE.md if structure changed
- Update CLAUDE.md if new patterns/commands discovered

### 4. Code Quality Gate
If code was modified this session:
- Run tests: `[TEST_COMMAND]`
- Run linter: `[LINT_COMMAND]`
- If either fails, file P0 issue and note in handoff

### 5. Git Checkpoint
- Stage and commit working code with descriptive message
- Do NOT commit failing tests (except intentional TDD red phase)

### 6. Sync Issue Tracker
- Run `bd sync` to ensure all issues are persisted
- Verify with `bd list --status open`

### 7. Push to Remote
- Rebase on latest remote: `git pull --rebase`
- Push your branch: `git push`
- Verify: `git status` (must show up to date with origin)

### 8. Create Pull Request (PR) to master
- If on `master`, do NOT create a PR
- If a PR already exists for this branch, do NOT create a duplicate
- Otherwise create a PR targeting `master`:
  - `gh pr create --base master --fill`

### 9. Generate Handoff
Provide a summary for the next session:
- What was accomplished
- What's in progress (with issue IDs)
- What's blocked and why
- Recommended next task: `bd ready --limit 1`

IMPORTANT: ALWAYS Output a ready-to-paste prompt within triple backticks (```) for starting the next session.
