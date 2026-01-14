---
description: Start-of-session protocol (preflight + select next work)
allowed-tools: Bash(git:*), Bash(bd:*), Bash(pytest:*), Read, Glob, Grep
argument-hint: "[--issue <id>]"
---

# Start Command

## Usage
```
/start [--issue <id>]
```

## Process

- Proceed autonomously without requesting approval unless a later step explicitly requires it.

1. Select next work.

- If `--issue <id>` provided:
  - Run `bd show <id>`.
- Otherwise:
  - Run `bd ready --limit 1`.
  - Choose the top unblocked issue and run `bd show <id>`.

2. Run session preflight.

**Canonical:** @/.claude/skills/session-preflight/SKILL.md

3. Claim the issue.

- Run `bd update <id> --status in_progress`.

4. Verify branch context.

- Ensure you are on a feature branch created from `origin/master` for this work unless explicitly requested for emergency work.

5. Plan before implementing.

- Use `/plan` if the scope is non-trivial.
- Follow strict TDD: tests before implementation.

6. Begin work.

- Start with the smallest failing test that moves the issue forward.

## Arguments

$ARGUMENTS - Optional issue selector (e.g. `--issue AIDEV-123` or numeric ID depending on bd config)
