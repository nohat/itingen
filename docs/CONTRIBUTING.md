# Contributing Guide

## Development Philosophy

This project maintains high quality through:
1. **Test-Driven Development (TDD)** - All features start with tests
2. **Anchor Comments** - Important context documented inline
3. **Small Commits** - One logical change per commit
4. **Documentation** - Code changes include doc updates

## Security: Secret Scanning

This repository uses automated secret scanning to prevent accidental commits of API keys and credentials.

### Detected Secret Types

The scanner checks for:
- **Google API Keys** (`AIza...`)
- **AWS Access Keys** (`AKIA...`)
- **GitHub Tokens** (`ghp_...`, `gho_...`, `ghu_...`, `ghs_...`)
- **Private Keys** (RSA, DSA, EC, OpenSSH, PGP)

### CI Integration

Secret scanning runs automatically in CI via pytest. Pull requests will fail if secrets are detected.

### Local Pre-Commit Hook (Optional)

To catch secrets before committing:

```bash
# Test the scanner
./scripts/check_secrets.sh

# To add to your workflow, call it before commits
# (The bd pre-commit hook handles beads sync automatically)
```

### If Secrets Are Detected

1. **Remove the secret** from the file immediately
2. **Rotate the key** - assume it's compromised
3. **Never commit secrets** - use `.env` files (in `.gitignore`)
4. **Check history** - if already pushed, consider `git filter-branch` or BFG Repo-Cleaner

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
1. **Create a Git worktree** using `bd` before starting work:
   ```bash
   bd worktree create <agent-id> --branch agent/<agent-id>
   cd .git/beads-worktrees/<agent-id>
   ```
2. **Work exclusively in the worktree** - never in the repository root if other agents are active.
3. **Use parallel execution** - multiple agents can work simultaneously via separate worktrees.
4. **Clean up after completion** - remove worktree and branch.

See [docs/agent-workspaces.md](agent-workspaces.md) for complete operating procedures.
