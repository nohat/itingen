# Land the Plane - Session End Protocol

## Usage
```
/project:land
```

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
