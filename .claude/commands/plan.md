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
