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
