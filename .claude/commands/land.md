---
description: Land the plane - session end protocol (capture work, commit, sync tracker)
allowed-tools: Bash(git:*), Bash(bd:*), Bash(npm:*), Bash(python:*), Read, Glob, Grep
---

# Land the Plane - Session End Protocol

## Usage
```
/land
```

## CRITICAL: AI Assistant Behavior

**MANDATORY EXECUTION**: This protocol MUST be executed at the end of EVERY session before stopping work. The AI assistant should NOT:

1. ❌ Stop work mid-task without landing
2. ❌ End sessions without completing this protocol  
3. ❌ Leave uncommitted changes
4. ❌ Leave the issue tracker out of sync

**AUTOMATIC TRIGGERS**: Execute this protocol when:
- User indicates session end ("I'm done", "that's all for today", etc.)
- User explicitly calls `/land`
- Natural conversation break points occur
- User requests to "stop", "pause", or "switch tasks"

**SESSION COMPLETION DEFINITION**: A session is ONLY complete when:
- All code changes are committed
- Issue tracker is synced (`bd sync` completed)
- Handoff summary is provided
- Git status shows "up to date with origin"

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

### 7. Generate Handoff
Provide a summary for the next session:
- What was accomplished
- What's in progress (with issue IDs)
- What's blocked and why
- Recommended next task: `bd ready --limit 1`

Output a ready-to-paste prompt for starting the next session.

### 8. Verify Completion
Before ending the session, verify:
- `git status` shows "up to date with origin" (no uncommitted changes)
- `bd list --status open` shows current work items
- All tests pass (if code was modified)
- No pending changes in working directory

**ONLY AFTER ALL STEPS ARE COMPLETE is the session truly finished.**
