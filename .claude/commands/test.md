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
