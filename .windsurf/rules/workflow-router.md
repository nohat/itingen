# Workflow Router

This rule routes Windsurf slash commands to their canonical definitions in `.claude/commands/`.

## Available Workflows

- **/start**: Start-of-session protocol. See `.windsurf/workflows/start.md`.
- **/land**: Session end protocol. See `.windsurf/workflows/land.md`.
- **/commit**: Git commit protocol. See `.windsurf/workflows/commit.md`.
- **/plan**: Work planning protocol. See `.windsurf/workflows/plan.md`.
- **/test**: Testing protocol. See `.windsurf/workflows/test.md`.
- **/review**: Code review protocol. See `.windsurf/workflows/review.md`.

## Instructions

When a user uses a slash command, consult the corresponding workflow file in `.windsurf/workflows/` or the command file in `.claude/commands/` and follow its instructions exactly.
If the user explicitly requests bypassing canonical workflow instructions, comply and note the deviation.
