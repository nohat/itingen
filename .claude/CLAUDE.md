# Trip Itinerary Generator - Claude Code Context

## Project Overview
A standalone, generic trip itinerary generation system extracted from scaffold project.
This system generates optimized travel itineraries based on venues, constraints, and preferences.

## CRITICAL WORKFLOW RULES

### Before ANY Code Changes
1. **ALWAYS** check for existing anchor comments: `grep -r "AIDEV-" src/`
2. **ALWAYS** run tests before AND after changes: `[TEST_COMMAND]`
3. **ALWAYS** commit working code before starting new features
4. **NEVER** modify tests to make them pass - fix the implementation instead
5. **NEVER** delete AIDEV-NOTE comments without explicit human approval

### Git Workflow
- Branch naming: `feat/description`, `fix/description`, `refactor/description`
- Commit format: `<emoji> <type>(<scope>): <description>`
- Commit emojis: ✨ feat | 🐛 fix | 📝 docs | ♻️ refactor | ✅ test | 🔧 chore
- ALWAYS commit after each successful test cycle
- NEVER commit failing tests (except intentionally in TDD red phase)

### Test-Driven Development (TDD) - MANDATORY
This project uses strict TDD. The cycle is:
1. **RED**: Write a failing test for the next small piece of functionality
2. **GREEN**: Write MINIMAL code to make the test pass
3. **REFACTOR**: Clean up while keeping tests green
4. **COMMIT**: Commit after each successful cycle

IMPORTANT: Do not write implementation before tests exist for it.

## Session Protocol

### Starting a Session
1. Run `bd ready` to see unblocked work
2. Review any handoff notes from previous session
3. Orient yourself with `grep -r "AIDEV-" src/` for context

### Ending a Session ("Land the Plane")
ALWAYS run `/land` before ending work. This ensures:
- Discovered work is captured in Beads
- Code is committed and tested
- Issue tracker is synced
- Next session has clear handoff

Never end a session with uncommitted work or unfiled issues.

## Anchor Comments System
Use these prefixed comments throughout the codebase:

- `AIDEV-NOTE:` - Important context for AI and developers (≤120 chars)
- `AIDEV-TODO:` - Work items that need attention
- `AIDEV-QUESTION:` - Uncertainties that need human clarification
- `AIDEV-DECISION:` - Records of architectural decisions made

Before scanning files, ALWAYS grep for `AIDEV-*` first to understand context.
Update relevant anchors when modifying associated code.
NEVER remove AIDEV-NOTE comments without explicit human instruction.

## Commands Reference
- `[PACKAGE_MANAGER] run build` - Build the project
- `[PACKAGE_MANAGER] run test` - Run all tests
- `[PACKAGE_MANAGER] run test:watch` - Run tests in watch mode
- `[PACKAGE_MANAGER] run lint` - Run linter
- `[PACKAGE_MANAGER] run typecheck` - Run type checker

## Code Style
- [TO BE DETERMINED based on source analysis]

## Architecture Patterns
- [TO BE DETERMINED based on source analysis]

## What AI Must NEVER Do
1. Skip the TDD cycle
2. Write large amounts of code without tests
3. Modify test assertions to make them pass
4. Remove anchor comments without permission
5. Commit directly to main branch
6. Make breaking changes without updating docs
7. Ignore failing tests
8. Over-engineer solutions beyond stated requirements
9. Implement speculative fallbacks or "just in case" error handling
10. Add backwards compatibility logic without a concrete, exercised use case
11. Blindly adopt inherited patterns without critical evaluation

## Domain Glossary
- **Venue**: A location that can be visited (restaurant, attraction, etc.)
- **Itinerary**: An ordered schedule of venue visits with timing
- **Constraint**: A rule that limits itinerary options (hours, distance, etc.)
- **Slot**: A time block in the itinerary
- [TO BE EXPANDED after source analysis]

## Inherited Technical Decisions
See `docs/INHERITED_DECISIONS.md` for architectural patterns and conventions
reviewed from the original scaffold project.

IMPORTANT: Inherited decisions are a STARTING POINT, not gospel. Critically evaluate
each decision against the needs of THIS project. Recommend overriding, modifying, or
deprecating patterns that don't serve our goals. Fresh code in a new project is an
opportunity to shed accumulated cruft.

## Engineering Philosophy

### Simplicity Over Accommodation
- **No speculative fallbacks**: Do not implement "just in case" error handling or
  graceful degradation unless there's a concrete, exercised use case
- **No legacy compatibility by default**: We're building fresh - don't carry forward
  backwards compatibility logic that will never be exercised
- **Fail fast, fail clearly**: Errors should be explicit and debuggable, not hidden
  behind best-effort recovery that masks root causes
- **Delete > Comment out > Keep**: When in doubt, remove code. Git remembers.

### The Fallback Test
Before implementing any fallback, recovery, or compatibility logic, ask:
1. Is this failure case actually expected in production?
2. Will this fallback be regularly exercised and tested?
3. Does the complexity cost justify the theoretical benefit?
4. Would a clear error message be more valuable than silent recovery?

If the answer to any is "no" or "maybe", DON'T implement the fallback.
Write a clear error instead and handle the case when it actually occurs.

### Technical Debt Philosophy
- Code that handles cases that "might happen someday" IS technical debt
- Untested fallback paths ARE bugs waiting to happen
- Complexity added for theoretical robustness REDUCES actual reliability
- Every branch in the code is a branch that needs testing and maintenance

## Issue Tracking
Use `bd` for all task tracking instead of markdown TODO lists.
- `bd create "Task" -p 1` - Create issue
- `bd ready` - Find unblocked work
- `bd close <id>` - Complete work
- `bd dep add <child> <parent>` - Track dependencies

File discovered work as you go. At session end, run `bd sync`.
