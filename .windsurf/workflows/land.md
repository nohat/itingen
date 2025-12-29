---
description: Land the plane - session end protocol (capture work, commit, sync tracker)
---

# Land the Plane - Session End Protocol

## Usage
`/land`

## Instructions
When this workflow is triggered, follow the session end protocol defined in `.claude/commands/land.md`.

## Process
1. **Capture Discovered Work:** Use `bd create` for new issues.
2. **Update Existing Issues:** Use `bd close` or `bd update`.
3. **Record Learnings:** Update documentation and code comments.
4. **Quality Gate:** Run tests and linters.
5. **Git Checkpoint:** Commit changes.
6. **Sync Tracker:** Run `bd sync`.
7. **Handoff:** Summarize progress and next steps.

Refer to @/Users/nohat/play/itingen/.claude/commands/land.md for detailed requirements.
