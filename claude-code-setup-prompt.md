# Comprehensive Claude Code Project Setup Prompt

## Initial Context for Claude Code

**Copy everything below this line into Claude Code:**

---

## CRITICAL: Read This First

Before writing ANY code, you MUST follow this structured setup process. Do not skip steps. Do not start coding until the planning phase is complete and I have explicitly approved the plan.

This is an empty directory. I want to extract itinerary generation capabilities from existing code and create a standalone, maintainable trip itinerary generation system.

## Source Files to Extract From

```
Source locations:
- /Users/nohat/scaffold/tools/nz_trip*
- /Users/nohat/scaffold/scaffold-data/data/nz_trip_venues
- /Users/nohat/scaffold/scaffold-data/tasks/new_zealand_trip

Technical decisions to incorporate:
- /Users/nohat/scaffold/scaffold-data/documents/TECHNICAL_DECISION*.md
```

## Phase 0: Project Infrastructure Setup

### Step 0.1: Initialize Git Repository

```bash
git init
git config user.name "$(git config --global user.name)"
git config user.email "$(git config --global user.email)"
```

Create initial `.gitignore`:
```
# Dependencies
node_modules/
venv/
.venv/
__pycache__/
*.pyc

# Environment
.env
.env.local
*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# Build outputs
dist/
build/
*.egg-info/

# Test artifacts
.coverage
htmlcov/
.pytest_cache/

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
tmp/
```

### Step 0.2: Create Directory Structure

```
trip-itinerary-generator/
├── .claude/
│   ├── CLAUDE.md                    # Main project context (auto-loaded)
│   ├── settings.json                # Project-specific settings
│   ├── commands/                    # Slash commands
│   │   ├── commit.md
│   │   ├── test.md
│   │   ├── review.md
│   │   └── plan.md
│   ├── agents/                      # Custom subagents
│   │   ├── planner.md
│   │   ├── reviewer.md
│   │   ├── tester.md
│   │   └── refactorer.md
│   └── skills/                      # Agent skills
│       └── tdd/
│           └── SKILL.md
├── docs/
│   ├── ARCHITECTURE.md              # System architecture decisions
│   ├── API.md                       # API documentation
│   ├── CONTRIBUTING.md              # How to contribute/maintain
│   ├── INHERITED_DECISIONS.md       # Decisions from original project
│   └── decisions/                   # Architecture Decision Records
│       └── 001-initial-architecture.md
├── src/                             # Source code
│   └── (to be determined after analysis)
├── tests/                           # Test files mirror src/ structure
├── scripts/                         # Utility scripts
├── .github/
│   └── workflows/                   # CI/CD (if needed later)
├── pyproject.toml                   # or package.json
├── README.md
└── CHANGELOG.md
```

### Step 0.3: Create CLAUDE.md (CRITICAL - Do this first!)

Create `.claude/CLAUDE.md` with the following content:

```markdown
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
```

### Step 0.4: Create Slash Commands

Create `.claude/commands/commit.md`:
```markdown
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
```

Create `.claude/commands/test.md`:
```markdown
# Run Tests Command

## Usage
```
/project:test [file_or_pattern]
```

## Process
1. If pattern provided, run only matching tests
2. Otherwise run full test suite
3. Display results with coverage summary
4. If failures:
   - Show failing test details
   - Suggest potential fixes based on error messages
   - Do NOT automatically fix without approval

## Arguments
$ARGUMENTS - Optional file path or test pattern

## Notes
- Always run tests in verbose mode for better debugging
- Report coverage changes compared to last run
```

Create `.claude/commands/review.md`:
```markdown
# Code Review Command

## Usage
```
/project:review [file_or_directory]
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
```

Create `.claude/commands/plan.md`:
```markdown
# Planning Command

## Usage
```
/project:plan <feature_or_task_description>
```

## Process
1. Research the codebase to understand current state
2. Identify affected files and components
3. Check for related AIDEV-* comments
4. Create a step-by-step implementation plan
5. Identify test cases needed (TDD approach)
6. Estimate complexity and potential risks
7. Present plan for approval BEFORE any implementation

## Output Format
```
## Feature: <name>

### Affected Areas
- file1.py - reason
- file2.py - reason

### Implementation Steps
1. [ ] Step 1 (tests first)
2. [ ] Step 2
...

### Test Cases Needed
- test_case_1: description
- test_case_2: description

### Risks & Considerations
- Risk 1
- Risk 2

### Questions for Human
- Question 1?
```

## Arguments
$ARGUMENTS - Feature or task description
```

### Step 0.5: Create Custom Subagents

Create `.claude/agents/planner.md`:
```markdown
---
name: planner
description: Research and planning agent for feature design. Invoked for exploration, architecture decisions, and creating implementation plans. READ-ONLY - does not modify files.
tools: Read, Glob, Grep
model: sonnet
---

# Planning Agent

You are a senior software architect focused on research and planning.

## Your Role
- Explore and understand codebases
- Identify patterns and existing conventions  
- Create detailed implementation plans
- Identify risks and edge cases
- Design test strategies

## You Must
- Always grep for AIDEV-* comments first
- Document your findings clearly
- Propose step-by-step plans
- Identify what tests are needed before implementation
- Flag uncertainties as AIDEV-QUESTION items

## You Must NOT
- Modify any files
- Write implementation code
- Make decisions without presenting options
- Skip the research phase
```

Create `.claude/agents/reviewer.md`:
```markdown
---
name: reviewer
description: Code review specialist. Invoked to review changes for quality, test coverage, and adherence to project standards. READ-ONLY.
tools: Read, Glob, Grep
model: sonnet
---

# Code Review Agent

You are a meticulous code reviewer focused on quality and maintainability.

## Review Checklist
- [ ] All new code has corresponding tests
- [ ] Tests follow the existing patterns
- [ ] AIDEV-NOTE comments on complex logic
- [ ] No hardcoded values that should be configurable
- [ ] Error handling is appropriate
- [ ] Documentation is updated
- [ ] No TODO/FIXME without AIDEV-TODO prefix
- [ ] Code follows project style guide

## Output Format
Structure your review as:
1. Summary (1-2 sentences)
2. ✅ Strengths
3. ⚠️ Suggestions  
4. ❌ Required Changes
5. Overall Assessment: APPROVE / REQUEST_CHANGES
```

Create `.claude/agents/tester.md`:
```markdown
---
name: tester
description: Test writing specialist for TDD workflow. Writes failing tests before implementation exists.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---

# TDD Test Writer Agent

You write tests BEFORE implementation exists. This is Test-Driven Development.

## TDD Rules
1. Write ONE failing test at a time
2. Test must fail for the RIGHT reason (missing implementation, not syntax error)
3. Test must be as simple as possible while still being meaningful
4. Do not mock things that don't exist yet
5. Do not write implementation code

## Test Writing Process
1. Understand the requirement
2. Write the simplest test that would force the implementation
3. Run the test - confirm it fails
4. STOP - return control to main agent for implementation

## Test Patterns
- One assertion per test when possible
- Descriptive test names: `test_<action>_<scenario>_<expected_result>`
- Arrange-Act-Assert structure
- Use fixtures for common setup
```

Create `.claude/agents/refactorer.md`:
```markdown
---
name: refactorer
description: Refactoring specialist. Improves code structure while maintaining all tests green.
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
---

# Refactoring Agent

You improve code structure without changing behavior. Tests must remain green.

## Refactoring Rules
1. Run tests BEFORE any changes
2. Make one small change at a time
3. Run tests AFTER each change
4. If tests fail, revert immediately
5. Commit after each successful refactoring

## Common Refactorings
- Extract method/function
- Rename for clarity
- Remove duplication (DRY)
- Simplify conditionals
- Extract constants
- Improve type hints

## You Must NOT
- Add new features
- Change test assertions
- Make changes that break tests
- Skip the test verification step
```

### Step 0.6: Create TDD Skill

Create `.claude/skills/tdd/SKILL.md`:
```markdown
---
name: tdd-workflow
description: Test-Driven Development workflow skill. Enforces red-green-refactor cycle.
---

# TDD Workflow Skill

This skill enforces strict Test-Driven Development practices.

## The TDD Cycle

### 1. RED Phase
- Write a failing test for the NEXT small piece of functionality
- The test MUST fail (if it passes, you wrote it wrong or the feature exists)
- The test should fail for the right reason (missing implementation)
- Run: `[TEST_COMMAND]` - verify failure
- DO NOT proceed until you have a properly failing test

### 2. GREEN Phase  
- Write the MINIMUM code to make the test pass
- No extra features, no "nice to haves"
- Code can be ugly - that's OK for now
- Run: `[TEST_COMMAND]` - verify pass
- If test fails, fix implementation NOT the test

### 3. REFACTOR Phase
- Now clean up the code
- Extract methods, improve names, remove duplication
- Run tests after EACH refactoring step
- If tests fail, REVERT the refactoring
- Only refactor when tests are green

### 4. COMMIT Phase
- Commit after each complete TDD cycle
- Commit message should reference what was added
- Include test file in the commit

## Verification Commands

Before implementation:
```bash
grep -r "AIDEV-" . --include="*.py" --include="*.ts" --include="*.js"
```

Run tests:
```bash
[TEST_COMMAND]
```

Check coverage:
```bash
[COVERAGE_COMMAND]
```

## Anti-Patterns to Avoid
- ❌ Writing tests after implementation
- ❌ Writing multiple tests before implementing any
- ❌ Modifying tests to make them pass
- ❌ Writing more code than needed to pass the test
- ❌ Skipping the refactor phase
- ❌ Not committing after each cycle
```

### Step 0.7: Create Project Settings

Create `.claude/settings.json`:
```json
{
  "allowedTools": [
    "Read",
    "Write", 
    "Edit",
    "Bash(npm:*)",
    "Bash(python:*)",
    "Bash(pytest:*)",
    "Bash(git:*)",
    "Bash(grep:*)",
    "Bash(find:*)",
    "Bash(cat:*)",
    "Bash(ls:*)"
  ],
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "echo '⚠️ File modified - remember to run tests'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Step 0.8: Create Initial Documentation

Create `README.md`:
```markdown
# Trip Itinerary Generator

A standalone system for generating optimized travel itineraries based on venues, constraints, and preferences.

## Features

[To be documented after initial development]

## Installation

[To be documented based on tech stack chosen]

## Usage

[To be documented with examples]

## Development

This project uses strict Test-Driven Development (TDD).

### Prerequisites
- [To be determined]

### Setup
```bash
# Clone the repository
git clone <repo-url>
cd trip-itinerary-generator

# Install dependencies
[INSTALL_COMMAND]

# Run tests
[TEST_COMMAND]
```

### TDD Workflow
1. Write a failing test
2. Write minimal code to pass
3. Refactor while green
4. Commit

See `.claude/skills/tdd/SKILL.md` for detailed TDD guidelines.

## Architecture

See `docs/ARCHITECTURE.md` for system design documentation.

## Contributing

See `docs/CONTRIBUTING.md` for guidelines.
```

Create `docs/CONTRIBUTING.md`:
```markdown
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
```

Create `docs/ARCHITECTURE.md`:
```markdown
# Architecture Documentation

## System Overview

[To be documented after source analysis]

## Core Components

[To be documented after source analysis]

## Data Flow

[To be documented after source analysis]

## Design Decisions

Architecture Decision Records (ADRs) are stored in `docs/decisions/`.

## Dependencies

[To be documented based on tech stack]
```

Create `docs/decisions/001-initial-architecture.md`:
```markdown
# ADR 001: Initial Architecture

## Status
Proposed

## Context
Extracting itinerary generation capabilities from the scaffold project into a standalone system.

## Decision
[To be documented after source analysis]

## Consequences
[To be documented]
```

Create `docs/INHERITED_DECISIONS.md` (template - to be filled in Step 1.1):
```markdown
# Inherited Technical Decisions

This document critically evaluates architectural decisions and patterns from the original 
scaffold project (`/Users/nohat/scaffold/`). We adopt what serves us, modify what partially
applies, and explicitly reject what doesn't fit our goals.

**Guiding Principle**: Fresh code is an opportunity. Don't inherit complexity that doesn't
earn its keep. When in doubt, start simple and add complexity only when proven necessary.

## Source Documents Reviewed
- [ ] TECHNICAL_DECISION*.md files from scaffold-data/documents/

## Decisions to Adopt (with justification)

### [Decision Name]
- **Source**: TECHNICAL_DECISION_xxx.md
- **Original Context**: [why it was made]
- **Why It Applies**: [specific benefit to THIS project]
- **Implementation Notes**: [any adaptations needed]

## Decisions to Modify

### [Decision Name]
- **Source**: TECHNICAL_DECISION_xxx.md
- **Original Decision**: [what it was]
- **What We're Changing**: [specific modification]
- **Why**: [concrete reason - not just "different context"]

## Decisions to REJECT

**Important**: Explicitly document rejected decisions so we don't accidentally re-adopt them.

### [Decision Name]
- **Source**: TECHNICAL_DECISION_xxx.md
- **Original Decision**: [what it was]
- **Why We Reject It**: [specific reason]
- **What We Do Instead**: [our approach, or "nothing - we don't need this"]

## Decisions to Deprecate (inherited but removing)

Patterns that were in the original code but we're intentionally NOT carrying forward:

### [Pattern/Approach]
- **Where It Existed**: [file/module]
- **Why It Existed**: [original justification]
- **Why We're Dropping It**: [specific reason - complexity, not needed, better approach exists]

## New Decisions Needed

### [Area/Topic]
- **Context**: [why we need a decision]
- **Options Considered**: [alternatives]
- **Recommendation**: [proposed approach]
- **Complexity Cost**: [what this adds to the codebase]
```

Create `CHANGELOG.md`:
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial project structure
- TDD workflow setup
- Claude Code configuration
```

---

## Optional Enhancement: Beads Issue Tracker

**Beads** is Steve Yegge's distributed, git-backed issue tracker designed specifically for AI coding agents. It solves the "50 First Dates" problem where agents lose context between sessions.

### Should You Use It?

**Use Beads if:**
- Project will span multiple sessions with complex, multi-step work
- You need to track discovered work, dependencies, and blocking issues
- You want persistent memory that survives context window limits
- Multiple agents or sessions might work on the project

**Skip Beads if:**
- This is a quick, single-session project
- The task list is simple enough for markdown checklists
- You want minimal tooling overhead

### Quick Setup (if using)

```bash
# Install Beads
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

# Initialize in project
bd init --quiet

# Add to CLAUDE.md (append):
echo "
## Issue Tracking
Use \`bd\` for all task tracking instead of markdown TODO lists.
- \`bd create \"Task\" -p 1\` - Create issue
- \`bd ready\` - Find unblocked work
- \`bd close <id>\` - Complete work
- \`bd list --json\` - Query issues
" >> .claude/CLAUDE.md
```

### Integration Notes
- Beads complements anchor comments (AIDEV-*) - use both
- AIDEV-TODO for inline "fix this here" notes
- Beads for tracked, queryable, cross-session work items
- Beads issues can reference anchor comments and vice versa

See: https://github.com/steveyegge/beads

---

## Phase 1: Source Analysis (DO THIS BEFORE CODING)

Now that the infrastructure is set up, analyze the source files:

### Step 1.1: Review Technical Decisions

**Start here first.** These documents contain architectural decisions and patterns from the original project. Your job is to CRITICALLY EVALUATE them, not blindly adopt them.

```
Ultrathink about this. Read and analyze all technical decision documents:

1. Read all files matching /Users/nohat/scaffold/scaffold-data/documents/TECHNICAL_DECISION*.md

For each document, CRITICALLY EVALUATE:
- What problem was this solving?
- Is that problem relevant to our standalone system?
- Is this the SIMPLEST solution, or is there accumulated complexity?
- Does this decision add fallback/compatibility logic we won't exercise?
- Would we make this same decision starting fresh today?

Be skeptical. Fresh code is an opportunity to shed cruft. Recommend REJECTING
decisions that add complexity without clear, concrete benefit to THIS project.

Create docs/INHERITED_DECISIONS.md with:
- Decisions to ADOPT (with specific justification for THIS project)
- Decisions to MODIFY (what we're changing and why)
- Decisions to REJECT (explicitly document what we're NOT doing)
- Decisions to DEPRECATE (patterns in original code we're intentionally dropping)
- New decisions needed for standalone system
```

### Step 1.2: Explore Source Files

Use the planner subagent or think hard about this:

```
Think hard about this task. First, I need you to explore and analyze the source files WITHOUT making any changes. 

Read and analyze these files:
1. All files matching /Users/nohat/scaffold/tools/nz_trip*
2. The directory /Users/nohat/scaffold/scaffold-data/data/nz_trip_venues
3. The directory /Users/nohat/scaffold/scaffold-data/tasks/new_zealand_trip

For each file:
- Document its purpose
- Identify key functions/classes
- Note dependencies
- Identify what's NZ-specific vs. generic
- Cross-reference with INHERITED_DECISIONS.md to see which patterns apply

Create a comprehensive analysis document at docs/SOURCE_ANALYSIS.md
```

### Step 1.3: Create Extraction Plan

After analysis, create a detailed extraction plan:

```
Based on the source analysis AND the inherited decisions, create a detailed plan in docs/EXTRACTION_PLAN.md:

1. What components can be extracted as-is?
2. What components need to be generalized?
3. What's the dependency order for extraction?
4. What tests exist that we should preserve?
5. What tests need to be written?
6. What's the proposed file structure?
7. Which architectural patterns from INHERITED_DECISIONS.md apply?
8. What new architectural decisions are needed?

Present this plan for my approval before any implementation.
```

### Step 1.4: Identify Test Cases

```
Before any implementation, identify all test cases needed:

1. Unit tests for each component
2. Integration tests for workflows
3. Edge cases and error conditions

Document these in docs/TEST_PLAN.md with:
- Test name
- What it validates
- Input scenarios
- Expected outputs
```

---

## Phase 2: Implementation (TDD - ONLY AFTER PLAN APPROVAL)

### Step 2.1: Set Up Test Infrastructure

```
Set up the testing framework and write the first test file structure.
Do NOT write implementation yet.

1. Install testing dependencies
2. Configure test runner
3. Create test directory structure mirroring src/
4. Write first failing test for the core data model
5. Commit: "✅ test: initial test infrastructure"
```

### Step 2.2: TDD Cycle for Each Component

For each component in the extraction plan:

```
Using strict TDD, implement [COMPONENT_NAME]:

1. RED: Write failing test(s) for the next small feature
2. Run tests - confirm failure
3. GREEN: Write minimal implementation to pass
4. Run tests - confirm pass  
5. REFACTOR: Clean up if needed (tests must stay green)
6. COMMIT: /project:commit

Repeat until component is complete.
```

### Step 2.3: Integration

```
After all components pass their unit tests:

1. Write integration tests for the full workflow
2. Implement any glue code needed
3. Verify all tests pass
4. Update documentation
5. Final commit
```

---

## Phase 3: Documentation & Cleanup

### Step 3.1: Update All Documentation

```
Review and update:
1. README.md - accurate installation and usage
2. docs/ARCHITECTURE.md - reflects actual implementation
3. docs/API.md - all public interfaces documented
4. CHANGELOG.md - all changes recorded
5. All AIDEV-NOTE comments are accurate
```

### Step 3.2: Final Review

```
/project:review

Verify:
- All tests pass
- Coverage is adequate
- No TODO/FIXME without AIDEV-TODO
- Documentation is complete
- Git history is clean
```

---

## Ongoing Maintenance Commands

When working on this project in the future, use these patterns:

### Starting a New Feature
```
/project:plan <feature description>
# Review plan, then:
# TDD cycle for implementation
```

### Quick Test Run
```
/project:test
```

### Before Committing
```
/project:review
/project:commit
```

### Understanding Code
```
grep -r "AIDEV-" src/
# Read relevant anchor comments first
```

---

## Remember These Principles

1. **Plan before code** - Use the planner subagent for any significant work
2. **TDD always** - No implementation without failing tests first
3. **Small commits** - One logical change, passing tests
4. **Anchor comments** - Document non-obvious decisions inline
5. **Update docs** - Documentation is part of the feature
6. **Ask when uncertain** - Create AIDEV-QUESTION comments

---

**START HERE:** Begin with Phase 0, Step 0.1. Create the git repository and proceed through the setup steps in order. Do not skip ahead to implementation until the infrastructure is complete and I've approved the extraction plan.
