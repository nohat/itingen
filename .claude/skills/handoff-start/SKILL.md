---
name: handoff-start
description: Start-of-session skill. Runs session preflight and then selects next work.
---

# Handoff Start Skill

This skill prevents "handoff priming" from bypassing safety checks.

## Process

### 1. Run preflight FIRST

Follow the `session-preflight` skill.

### 2. Only after preflight is complete

Run:
```bash
bd ready --limit 1
```

### 3. Confirm task context

Before implementing:
- Confirm issue ID and scope.
- Create/verify the correct feature branch.
- Use strict TDD (tests before implementation).
