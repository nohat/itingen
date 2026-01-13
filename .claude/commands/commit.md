---
description: Create a git commit with formatted message and tests
allowed-tools: Bash(git:*), Bash(npm:*), Bash(python:*), Bash(pytest:*)
argument-hint: "[--no-verify]"
---

# Git Commit Command

## Usage
```
/commit [--no-verify]
```

## Process
### 1. Branch Check
- Verify that you are NOT on `master`.
- If on `master`, switch to a feature branch: `git checkout -b <type>/<description>`.
- If work exists on `master`, move it to the branch before proceeding.

### 2. Stage Changes
- Check for unstaged changes, stage if appropriate.

### 3. Run Tests
- Run the full test suite - ABORT if tests fail.

### 4. Run Linter
- Run linter - fix any auto-fixable issues.

### 5. Analyze Diff
- Analyze diff for logical change groupings.
- If multiple unrelated changes, suggest splitting the commit.

### 6. Generate Message
- Generate commit message in format: `<emoji> <type>(<scope>): <description>`.
- Show the commit message for approval before committing.

### 7. Commit
- Create the commit.

### 8. Push to Remote
- Push the current branch: `git push origin <branch_name>`.
- Run `bd sync` to update the issue tracker state on the remote.

## Commit Types
- ✨ feat: New feature
- 🐛 fix: Bug fix
- 📝 docs: Documentation
- ♻️ refactor: Code restructuring
- ✅ test: Tests
- 🔧 chore: Build/tools

## Rules
- First line <72 chars
- Atomic commits (single logical purpose)
- Include AIDEV-NOTE if significant context needed
