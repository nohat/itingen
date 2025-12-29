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
