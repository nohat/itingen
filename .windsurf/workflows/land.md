---
description: Land the plane - session end protocol (capture work, commit, sync tracker)
---

# Land the Plane - Session End Protocol

## Usage
`/land`

### 1. Stage Changes
- Check for unstaged changes, stage if appropriate.

### 2. Run Tests
- Run the full test suite - ABORT if tests fail.

### 3. Git Checkpoint
- **Branch Check**: Prefer a feature branch for regular work.
- If on `master`, switch to a feature branch unless explicitly requested for emergency work: `git checkout -b <type>/<description>`.
- Stage and commit working code with descriptive message.
- Avoid committing directly to `master` unless explicitly requested for emergency work.
- Push the branch to remote: `git push origin <branch_name>`.
- Do NOT commit failing tests (except intentional TDD red phase).

### 4. Capture Discovered Work
- Use `bd create` for new issues.
- Use `bd close` or `bd update` for existing issues.

### 5. Record Learnings
- Update documentation and code comments.

### 6. Sync Tracker
- Run `bd sync`.

### 7. Handoff
- Summarize progress and next steps.

Refer to @/.claude/commands/land.md for detailed requirements.
