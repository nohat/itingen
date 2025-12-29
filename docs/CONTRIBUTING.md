# Contributing Guide

## Development Philosophy

This project maintains high quality through:
1. **Test-Driven Development (TDD)** - All features start with tests
2. **Anchor Comments** - Important context documented inline
3. **Small Commits** - One logical change per commit
4. **Documentation** - Code changes include doc updates

## Workflow for New Features

1. **Plan First**
   ```
   /project:plan <feature description>
   ```

2. **Write Tests** (TDD Red Phase)
   - Use the tester subagent or write manually
   - Run tests to confirm they fail

3. **Implement** (TDD Green Phase)
   - Write minimal code to pass tests
   - Run tests frequently

4. **Refactor** (TDD Refactor Phase)
   - Clean up code structure
   - Keep tests green

5. **Review**
   ```
   /project:review
   ```

6. **Commit**
   ```
   /project:commit
   ```

## Anchor Comment Guidelines

Add `AIDEV-NOTE:` comments when code is:
- Complex or non-obvious
- A workaround for an edge case
- Critical to system behavior
- Likely to confuse future developers/AI

## Code Style

[To be documented based on tech stack]

## Cascade Agent Workflow

Cascade agents are expected to:
1. **Create a Git worktree** before starting work:
   ```bash
   git worktree add .ws/<agent-id> -b agent/<agent-id>
   cd .ws/<agent-id>
   ```
2. **Work exclusively in the worktree** - never in the repository root
3. **Use parallel execution** - multiple agents can work simultaneously
4. **Clean up after completion** - remove worktree and branch

See [docs/agent-workspaces.md](agent-workspaces.md) for complete operating procedures.
