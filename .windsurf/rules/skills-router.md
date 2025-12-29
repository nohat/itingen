# Skills Router

This rule instructs the assistant on how to handle capabilities defined as skills in the `.claude/skills/` directory.

## Instructions

1.  **Consult the Index:** Always check `.windsurf/rules/skills-index.generated.md` to see available skills.
2.  **Follow Canonical Docs:** When a skill is relevant to a user request, open and follow the instructions in the canonical `SKILL.md` file listed in the index.
3.  **Do Not Duplicate:** Do not copy skill logic into Windsurf rules. Use the canonical documents as the single source of truth.
4.  **Execute via CLI:** Skills typically define CLI entrypoints. Execute these as specified in the `SKILL.md` file.

## Available Skills

See `.windsurf/rules/skills-index.generated.md` for the current list of indexed skills.
