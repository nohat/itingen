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
