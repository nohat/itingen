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

## Canonical References

- Skills router: `@/Users/nohat/play/itingen/.windsurf/rules/skills-router.md`
- Skills index (generated): `@/Users/nohat/play/itingen/.windsurf/rules/skills-index.generated.md`
- Workflow router: `@/Users/nohat/play/itingen/.windsurf/rules/workflow-router.md`
- Architecture: `@/Users/nohat/play/itingen/docs/ARCHITECTURE.md`
