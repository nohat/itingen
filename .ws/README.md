# Agent Workspace Directory

This directory (`.ws/`) is reserved for **Cascade agent Git worktrees**.

## Purpose

Each subdirectory here represents a separate Git worktree used by an individual Cascade agent. This mechanism enables:

- **Parallel execution**: Multiple agents can work simultaneously without conflicts
- **Isolation**: Each agent operates in its own filesystem space and branch
- **Clean coordination**: Agents interact via Git review, not shared state

## Structure

```
.ws/
├── agent-001/          # Worktree for agent-001 (branch: agent/agent-001)
├── weather-optimizer/  # Worktree for weather-optimizer (branch: agent/weather-optimizer)
└── renderer-v2/        # Worktree for renderer-v2 (branch: agent/renderer-v2)
```

## Usage

**Agents must create their own worktree before starting work:**

```bash
# From repository root
git worktree add .ws/<agent-id> -b agent/<agent-id>
cd .ws/<agent-id>
```

## Important

- Contents are **ephemeral** and never committed to the repository
- Only this README file is tracked
- Worktrees are removed after merge or discard:
  ```bash
  git worktree remove .ws/<agent-id>
  git branch -d agent/<agent-id>
  ```

## For Humans

To inspect agent work:
```bash
cd .ws/<agent-id>
git log --oneline
git diff main
```

To clean up abandoned worktrees:
```bash
git worktree prune
```
