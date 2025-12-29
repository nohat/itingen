# Git Commit Command

## Usage
```
/project:commit [--no-verify]
```

## Process
1. Check for unstaged changes, stage if appropriate
2. Run the full test suite - ABORT if tests fail
3. Run linter - fix any auto-fixable issues
4. Analyze diff for logical change groupings
5. If multiple unrelated changes, suggest splitting the commit
6. Generate commit message in format: `<emoji> <type>(<scope>): <description>`
7. Show the commit message for approval before committing
8. Create the commit

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
