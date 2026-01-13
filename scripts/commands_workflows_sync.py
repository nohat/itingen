import argparse
from pathlib import Path


AUTO_MARKER = "<!-- AUTO-GENERATED: commands_workflows_sync.py -->"


def extract_frontmatter_description(content: str) -> str | None:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            break
        if lines[i].startswith("description:"):
            return lines[i].split(":", 1)[1].strip().strip('"').strip("'")

    return None


def title_from_name(name: str) -> str:
    # "start" -> "Start", "my-command" -> "My Command"
    return " ".join(p.capitalize() for p in name.replace("_", "-").split("-"))


def is_generated_workflow(path: Path) -> bool:
    try:
        content = path.read_text()
    except OSError:
        return False
    return AUTO_MARKER in content


def render_workflow(name: str, description: str | None, command_abs_path: Path) -> str:
    desc = description or f"Workflow wrapper for /{name}"
    title = title_from_name(name)

    return (
        "---\n"
        f"description: {desc}\n"
        "---\n\n"
        f"{AUTO_MARKER}\n\n"
        f"# {title} Workflow\n\n"
        "## Usage\n"
        f"`/{name}`\n\n"
        "## Instructions\n"
        f"Follow the instructions in @/{command_abs_path} exactly.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync .claude/commands to .windsurf/workflows wrappers")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing workflow files if they are marked as auto-generated",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    commands_dir = project_root / ".claude" / "commands"
    workflows_dir = project_root / ".windsurf" / "workflows"

    workflows_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    overwritten = 0

    for command_path in sorted(commands_dir.glob("*.md")):
        name = command_path.stem
        workflow_path = workflows_dir / f"{name}.md"

        description = extract_frontmatter_description(command_path.read_text())

        if workflow_path.exists():
            if args.force and is_generated_workflow(workflow_path):
                workflow_path.write_text(render_workflow(name, description, command_path))
                overwritten += 1
            else:
                skipped += 1
            continue

        workflow_path.write_text(render_workflow(name, description, command_path))
        created += 1

    print(
        f"commands_workflows_sync: created={created} overwritten={overwritten} skipped={skipped} "
        f"(force={'on' if args.force else 'off'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
