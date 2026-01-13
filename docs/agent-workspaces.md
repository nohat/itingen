# Agent Workspace Operating Standard

## Overview

This repository supports **parallel Cascade agents** through Git worktrees. Each agent operates in an isolated worktree with its own branch, enabling concurrent development without filesystem conflicts.

## Model

### One Agent = One Worktree = One Branch

```
Repository Root (not for agent work)
├── src/
├── docs/
├── .ws/                    # Agent worktree directory
│   ├── agent-001/          # Agent 001 worktree
│   │   └── (branch: agent/agent-001)
│   └── data-cleaner/       # Data cleaner worktree
│       └── (branch: agent/data-cleaner)
```

### Invariants

1. **Isolation**: Agents never share worktrees or branches.
2. **Coordination via Git**: All interaction happens through pull requests/reviews.
3. **Ephemerality**: Worktrees are temporary, branches persist for review.
4. **No direct modifications to master**: Agents never work directly in `master`.
5. **Standard Location**: Worktrees are managed by `bd` and located in `.git/beads-worktrees/` by default.

## Why bd worktree

`bd worktree` provides:
- **Filesystem isolation**: Each agent has its own working directory.
- **Branch isolation**: Work is automatically separated by branch.
- **Beads Integration**: Automatically sets up the beads redirect so the issue database is shared.
- **Native Git**: Wraps native git worktree commands with project-specific logic.

## Required Agent Bootstrap Procedure

**Every Cascade agent MUST execute these steps before starting work:**

```bash
# 1. Create worktree with dedicated branch using bd
bd worktree create <agent-id> --branch agent/<agent-id>

# 2. Enter the worktree
cd .git/beads-worktrees/<agent-id>

# 3. Verify isolation
git branch  # Should show agent/<agent-id>
git status  # Should show clean worktree
```

### Agent ID Format

- Use descriptive names: `weather-integration`, `pdf-renderer`, `data-validator`
- Use hyphens, not underscores
- Keep under 50 characters
- Prefix with `agent/` for branch names

## Human Operations

### Reviewing Agent Work

```bash
# List all worktrees
git worktree list

# Inspect specific agent work
cd .ws/<agent-id>
git log --oneline main..HEAD
git diff main..HEAD
```

### Merging Agent Work

```bash
# From repository root (or any location)
git checkout master
git merge agent/<agent-id>
git push origin master
```

### Cleanup After Merge/Discard

```bash
# Remove worktree using bd
bd worktree remove <agent-id>

# Delete branch after merge
git branch -d agent/<agent-id>

# Clean up any stale worktrees
git worktree prune
```

## Agent Coordination Rules

### DO

- Create worktree before any code changes
- Work exclusively in your worktree
- Commit frequently with clear messages
- Create pull requests for review
- Clean up worktree after completion

### DO NOT

- Work directly in `master` branch.
- Share worktrees between agents.
- Commit to `master` branch directly.
- Leave abandoned worktrees.
- Modify files outside your worktree.

## Troubleshooting

### Worktree Already Exists

```bash
# Check if worktree is already present
git worktree list

# If worktree exists but branch is missing
git worktree add .ws/<agent-id> --force
```

### Stale Worktree References

```bash
# Clean up orphaned worktree references
git worktree prune
```

### Branch Already Exists

```bash
# Use existing branch
git worktree add .ws/<agent-id> agent/<agent-id>
```

## Integration with CI/CD

- CI runs on all `agent/*` branches
- Pull requests required for merging to main
- Automated tests run on each push to agent branches

## Security Considerations

- Worktrees have access to entire repository history
- No additional isolation beyond Git permissions
- Agent credentials should be scoped appropriately
- Sensitive configuration remains in main branch

## Migration from Single-Agent Workflow

Previous single-agent workflow (working directly in repository root) is deprecated. All agents must migrate to worktree-based workflow:

1. Create worktree for existing work
2. Move uncommitted changes to worktree
3. Clean repository root
4. Continue in worktree

This ensures consistent behavior across all agents and prevents accidental conflicts.
