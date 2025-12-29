# Claude Code Best Practices Reference

This document supplements the main setup prompt with additional patterns, tips, and advanced techniques gathered from the agentic coding community.

---

## Table of Contents

1. [Thinking Triggers](#thinking-triggers)
2. [Context Management](#context-management)
3. [Beads: Structured Task Memory](#beads-structured-task-memory)
4. [Feedback Loop Patterns](#feedback-loop-patterns)
5. [Git Workflow Automation](#git-workflow-automation)
6. [Preventing Agent Drift](#preventing-agent-drift)
7. [Advanced Hook Patterns](#advanced-hook-patterns)
8. [Multi-Agent Workflows](#multi-agent-workflows)
9. [Engineering Philosophy](#engineering-philosophy)
10. [Troubleshooting](#troubleshooting)

---

## Thinking Triggers

Claude Code supports extended thinking mode with specific trigger phrases that allocate progressively more thinking budget:

| Phrase | Thinking Level | Use Case |
|--------|---------------|----------|
| "think" | Low | Simple problems |
| "think hard" | Medium | Moderate complexity |
| "think harder" / "think very hard" | High | Complex problems |
| "ultrathink" / "megathink" | Maximum | Architecture decisions, complex debugging |

**Best Practice:** Use "ultrathink" or "think very hard" for:
- Initial project planning
- Architecture decisions
- Complex bug diagnosis
- Before any significant refactoring

Example prompts:
```
"Ultrathink about the best architecture for this itinerary system"
"Think very hard about edge cases in the scheduling algorithm"
"Think hard about how to structure these tests"
```

---

## Context Management

### The `/clear` Strategy

Use `/clear` liberally to reset context between tasks. A cluttered context window degrades performance.

**When to clear:**
- After completing a feature
- When switching between unrelated tasks
- If Claude seems confused or repetitive
- After large file operations

### Progressive Disclosure in Skills

Structure skills to load information on-demand:

```
skill/
├── SKILL.md           # Metadata + entry point (always loaded)
├── patterns/          # Loaded when pattern matching needed
│   ├── api.md
│   └── data.md
├── templates/         # Loaded when generating code
│   └── component.template
└── scripts/          # Executed only when needed
    └── validate.sh
```

### Subagent Context Isolation

Use subagents to prevent context pollution:

```markdown
# In your prompt:
"Use a subagent to explore the authentication module and report back 
with a summary. Keep the main context clean for implementation."
```

This is especially important for:
- Large codebase exploration
- Research tasks
- Parallel investigations

---

## Beads: Structured Task Memory

[Beads](https://github.com/steveyegge/beads) is Steve Yegge's distributed, git-backed issue tracker designed specifically for AI coding agents. It replaces unstructured markdown TODO files with queryable, dependency-aware task tracking.

### The Problem Beads Solves

From Yegge's analysis: Agents create markdown plans that look organized but fail in practice because:
- Markdown is text, not structured data - parsing steals compute from your actual problem
- Plans aren't queryable - hard to build a work queue or audit progress
- No dependency tracking - agents can't tell what's blocked
- No cross-session memory - agents forget between conversations

### Core Features

```bash
# Git-backed storage (.beads/ directory, committed to repo)
# SQLite cache for fast queries
# Four dependency types: blocks, related, parent-child, discovered-from
# "Ready work" detection - finds unblocked issues
# Hash-based IDs prevent merge conflicts in multi-agent workflows
# Memory decay - auto-summarizes old closed issues
```

### When to Use Beads vs. Anchor Comments

| Use Case | Tool |
|----------|------|
| "Fix this specific line" | AIDEV-TODO inline comment |
| "This is weird because X" | AIDEV-NOTE inline comment |
| "We need to implement feature Y" | Beads issue |
| "Task A blocks Task B" | Beads dependency |
| Cross-session work queue | Beads `bd ready` |
| Local context for this code | Anchor comment |

**Best practice**: Use both. Anchor comments for inline context, Beads for tracked work items.

### Integration with Claude Code

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

# Initialize (run once per project)
bd init --quiet

# Agent workflow
bd ready --json | jq '.[0]'          # Get next task
bd create "Bug found" -p 1 -t bug    # Track discovered work
bd dep add <new> <parent> --type discovered-from
bd close <id> --reason "Fixed"       # Complete work
```

### Session End Pattern (from Yegge)

At end of each session, tell the agent: "Let's land the plane."

This triggers:
1. File/update issues for remaining work
2. Sync the issue tracker (`bd sync`)
3. Generate next-session prompt from `bd ready`

### Evaluation for Your Project

**Adopt Beads if:**
- ✅ Multi-session project with complex task dependencies
- ✅ Need to track "discovered work" during development
- ✅ Want queryable work queue across sessions
- ✅ Multiple agents might work in parallel

**Skip Beads if:**
- ❌ Single-session, simple task
- ❌ Markdown checklists are sufficient
- ❌ Minimizing tool dependencies is priority

---

## Feedback Loop Patterns

### Automated Test Feedback

Configure hooks to run tests automatically:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/quick-test.sh $CLAUDE_FILE_PATH",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

### Screenshot Iteration Loop

For UI work, establish a visual feedback loop:

1. Configure Puppeteer or similar screenshot tool
2. Give Claude the design mock
3. Ask Claude to:
   - Implement
   - Screenshot the result
   - Compare to mock
   - Iterate until matching

### Build/Lint Feedback

Create a pre-commit validation hook:

```bash
#!/bin/bash
# scripts/validate.sh

# Run linter
npm run lint --fix
if [ $? -ne 0 ]; then
    echo "❌ Lint failed"
    exit 1
fi

# Run type check
npm run typecheck
if [ $? -ne 0 ]; then
    echo "❌ Type check failed"
    exit 1
fi

# Run tests
npm run test
if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi

echo "✅ All checks passed"
```

---

## Git Workflow Automation

### Conventional Commits Command

Create `.claude/commands/commit.md` with emoji mapping:

```markdown
## Emoji Reference
| Type | Emoji | Description |
|------|-------|-------------|
| feat | ✨ | New feature |
| fix | 🐛 | Bug fix |
| docs | 📝 | Documentation |
| style | 💄 | Formatting |
| refactor | ♻️ | Code restructuring |
| perf | ⚡ | Performance |
| test | ✅ | Tests |
| chore | 🔧 | Build/tools |
| ci | 🚀 | CI/CD |
| security | 🔒 | Security fix |
| breaking | 💥 | Breaking change |
| wip | 🚧 | Work in progress |
| revert | ⏪ | Revert changes |
```

### Branch Protection Pattern

Add to CLAUDE.md:

```markdown
## Git Rules
- NEVER commit directly to `main` or `develop`
- Always create feature branches: `feat/<ticket>-<description>`
- Squash commits before merge
- Delete branch after merge
```

### Automated Co-author Attribution

Hook to add co-author to commits:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'git commit'; then export GIT_AUTHOR_NAME='Developer'; fi"
          }
        ]
      }
    ]
  }
}
```

---

## Preventing Agent Drift

### The Anchor Comment System

Anchor comments are inline documentation that Claude writes and maintains for itself.

**Standard prefixes:**
```python
# AIDEV-NOTE: This cache invalidation is intentionally eager due to [reason]
# AIDEV-TODO: Refactor this when async support is added
# AIDEV-QUESTION: Should this handle negative values?
# AIDEV-DECISION: Using factory pattern here because [reason]
# AIDEV-WARNING: Do not modify without updating [related_file]
```

**In CLAUDE.md, instruct:**
```markdown
## Anchor Comment Protocol
Before modifying any file:
1. `grep -r "AIDEV-" <file_path>`
2. Read and understand all anchors
3. Update anchors if your changes affect them
4. Add new anchors for:
   - Complex logic
   - Non-obvious decisions
   - Workarounds
   - Critical dependencies
```

### Task Checklists for Complex Work

For multi-step tasks, use a markdown checklist:

```markdown
Create a checklist file `tasks/current.md`:

## Feature: User Authentication
- [ ] Write test for login endpoint
- [ ] Implement login endpoint
- [ ] Write test for token validation
- [ ] Implement token validation
- [ ] Write integration test
- [ ] Update API documentation
- [ ] Add AIDEV-NOTE for auth flow

Check off items as you complete them. Do not skip ahead.
```

### The "What NOT to Do" Section

Always include explicit prohibitions in CLAUDE.md:

```markdown
## What AI Must NEVER Do
1. Delete files without explicit approval
2. Modify test assertions to make tests pass
3. Remove AIDEV-* comments
4. Skip the TDD cycle
5. Make changes outside the current task scope
6. Use `any` type in TypeScript
7. Commit with failing tests
8. Push to protected branches
```

### Scope Boundaries

Define clear boundaries for each session:

```markdown
## Current Session Scope
Working on: Venue data model
Files allowed to modify:
- src/models/venue.py
- tests/test_venue.py

Files NOT to modify:
- src/models/itinerary.py (next task)
- Any configuration files
```

---

## Advanced Hook Patterns

### Pre-Commit Validation Hook

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$CLAUDE_TOOL_INPUT\" | jq -r '.command' | grep -q '^git commit'; then ./scripts/pre-commit.sh; fi",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

### File Modification Logging

Track all file changes:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$(date): Modified file\" >> .claude/activity.log"
          }
        ]
      }
    ]
  }
}
```

### Notification on Completion

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude finished\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

---

## Multi-Agent Workflows

### Parallel Git Worktrees

For truly parallel work:

```bash
# Create worktrees for parallel development
git worktree add ../project-auth feature/auth
git worktree add ../project-api feature/api
git worktree add ../project-ui feature/ui

# Run Claude in each worktree in separate terminals
cd ../project-auth && claude
cd ../project-api && claude  
cd ../project-ui && claude
```

### Writer-Reviewer Pattern

Two-Claude review workflow:

1. **Claude A (Writer):** Implements feature
2. **Claude B (Reviewer):** Reviews in fresh context

```bash
# Terminal 1: Implementation
claude "Implement the venue search feature using TDD"

# Terminal 2: Fresh review
claude "Review the changes in the last 3 commits. 
Check for: missing tests, edge cases, documentation gaps"
```

### Orchestrated Multi-Agent

For complex features, orchestrate multiple subagents:

```markdown
# In your prompt:
"For this feature:
1. Use @planner to create the implementation plan
2. Use @tester to write the failing tests  
3. [I will review tests]
4. Implement the feature
5. Use @reviewer to check the implementation
6. Use @refactorer if cleanup is needed"
```

---

## Engineering Philosophy

These principles guide architectural decisions and code quality in agentic coding workflows.

### Simplicity Over Accommodation

**Core principle**: Don't implement complexity for theoretical scenarios. Add it when reality demands it.

```markdown
❌ BAD: "Let's add a fallback in case the API returns malformed data"
✅ GOOD: "If the API returns malformed data, fail with a clear error. 
   We'll handle it if it actually happens."

❌ BAD: "We should support both the old and new format for backwards compatibility"
✅ GOOD: "We only support the new format. We're starting fresh."

❌ BAD: "Let's add graceful degradation if the database is slow"
✅ GOOD: "If the database is slow, that's a bug to fix, not hide."
```

### The Fallback Test

Before implementing ANY fallback, recovery, or compatibility logic:

1. **Is this failure case actually expected in production?**
   - If "maybe" or "just in case" → Don't implement
   
2. **Will this fallback be regularly exercised and tested?**
   - Untested fallback paths ARE bugs → Don't implement

3. **Does the complexity cost justify the benefit?**
   - Every branch needs maintenance → Be skeptical

4. **Would a clear error be more valuable?**
   - Errors you can debug > Silent recovery that hides problems

### Anti-Patterns to Avoid

```python
# ❌ Speculative error handling
try:
    result = api.call()
except SomeError:
    # "Just in case" - but when does this actually happen?
    result = fallback_value  

# ✅ Explicit failure
result = api.call()  # If it fails, we'll see it and fix it

# ❌ Legacy compatibility
if old_format(data):
    data = convert_to_new(data)  # Will this ever run?
process(data)

# ✅ Clean contract
if not valid_format(data):
    raise ValueError(f"Invalid format: {data}")
process(data)

# ❌ Best-effort recovery
def parse(text):
    try:
        return strict_parse(text)
    except:
        return fuzzy_parse(text)  # Masks real bugs

# ✅ Fail fast
def parse(text):
    return strict_parse(text)  # Clear error if format wrong
```

### Technical Debt Wisdom

- Code for hypothetical scenarios IS technical debt
- Untested code paths ARE bugs waiting to happen  
- Complexity for "robustness" REDUCES reliability
- When in doubt: Delete it. Git remembers.

---

## Troubleshooting

### Common Issues

**Claude keeps going off-track:**
- Add more explicit constraints to CLAUDE.md
- Use the anchor comment system
- Create scope boundaries
- Use `/clear` more frequently

**Tests keep breaking:**
- Ensure strict TDD discipline
- Add hook to run tests after every edit
- Use @reviewer to catch issues

**Context getting polluted:**
- Use subagents for exploration
- Clear context between tasks
- Structure skills for progressive disclosure

**Git conflicts:**
- Use git worktrees for parallel work
- Commit more frequently
- Smaller, atomic changes

### Debug Mode

Add verbose logging:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"PRE: $CLAUDE_TOOL_NAME\" >> .claude/debug.log"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"POST: $CLAUDE_TOOL_NAME\" >> .claude/debug.log"
          }
        ]
      }
    ]
  }
}
```

### Recovery Patterns

**When implementation goes wrong:**
1. Use `/rewind` to go back to a good state
2. Or `git stash` / `git reset --hard`
3. Re-approach with clearer constraints
4. Consider using "ultrathink" for replanning

**When tests are failing mysteriously:**
1. Run tests in isolation
2. Check for state pollution between tests
3. Use @planner to analyze the test structure
4. Add more granular assertions to identify the exact failure

---

## Quick Reference Card

### Essential Slash Commands
```
/project:plan <feature>    - Plan before implementing
/project:test [pattern]    - Run tests
/project:review [path]     - Code review
/project:commit           - Smart commit
/clear                    - Reset context
/rewind                   - Go back in history
```

### Essential Thinking Triggers
```
"think"           - Light analysis
"think hard"      - Moderate complexity
"ultrathink"      - Maximum depth
```

### Essential Grep Patterns
```
grep -r "AIDEV-" src/              - Find all anchor comments
grep -r "AIDEV-TODO" .             - Find all TODOs
grep -r "AIDEV-QUESTION" .         - Find uncertainties
```

### TDD Cycle Reminder
```
1. RED:      Write failing test
2. GREEN:    Minimal implementation
3. REFACTOR: Clean up (tests green)
4. COMMIT:   Save progress
```

---

## Sources & Further Reading

### Core Documentation
- [Anthropic's Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Anthropic's Agent Skills Documentation](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### Workflow Patterns
- [Field Notes from Shipping Real Code with Claude](https://www.lesswrong.com/posts/dxiConBZTd33sFaRC/field-notes-from-shipping-real-code-with-claude) - Anchor comments pattern
- [Armin Ronacher's Agentic Coding Recommendations](https://lucumr.pocoo.org/2025/6/12/agentic-coding/)

### Task Tracking & Memory
- [Beads: A Memory Upgrade for Coding Agents](https://github.com/steveyegge/beads) - Steve Yegge's distributed issue tracker
- [Introducing Beads](https://steve-yegge.medium.com/introducing-beads-a-coding-agent-memory-system-637d7d92514a) - Why markdown plans fail
- [Beads Best Practices](https://steve-yegge.medium.com/beads-best-practices-2db636b9760c) - Session management patterns

### Testing & Quality
- [TDD Guard for Claude Code](https://github.com/nizos/tdd-guard)
- [Forcing Claude Code to TDD](https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/) - Subagent-based TDD enforcement

### Tool Collections
- [Awesome Claude Code Collection](https://github.com/hesreallyhim/awesome-claude-code)
- [Claude Command Suite](https://github.com/qdhenry/Claude-Command-Suite) - 148+ slash commands
- [IndyDevDan's Claude Code Tutorials](https://www.youtube.com/@indydevdan)
