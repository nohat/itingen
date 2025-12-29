---
description: Review code for bugs, tests, style, and security
allowed-tools: Bash(git:*), Bash(grep:*), Read, Glob, Grep
argument-hint: "[file_or_directory]"
---

# Code Review Command

## Usage
```
/review [file_or_directory]
```

## Process
1. Analyze the specified code (or recent changes if not specified)
2. Check for:
   - Missing tests
   - Missing AIDEV-NOTE comments on complex code
   - Potential bugs or edge cases
   - Code style violations
   - Performance issues
   - Security concerns
3. Verify documentation is up to date
4. Check that all AIDEV-TODO items are addressed or documented

## Output Format
Provide a structured review with:
- ✅ What's good
- ⚠️ Suggestions for improvement
- ❌ Issues that must be fixed
- 📝 Documentation gaps

## Arguments
$ARGUMENTS - Optional path to review
