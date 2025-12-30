import re
from pathlib import Path

def extract_frontmatter(content):
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {}
    
    yaml_text = match.group(1)
    metadata = {}
    for line in yaml_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata

def generate_index():
    project_root = Path(__name__).parent.parent.absolute()
    skills_dir = project_root / ".claude" / "skills"
    rules_dir = project_root / ".windsurf" / "rules"
    
    if not rules_dir.exists():
        rules_dir.mkdir(parents=True)
    
    skills = []
    if skills_dir.exists():
        for skill_path in skills_dir.rglob("SKILL.md"):
            with open(skill_path, 'r') as f:
                content = f.read()
                metadata = extract_frontmatter(content)
                name = metadata.get('name', skill_path.parent.name)
                description = metadata.get('description', 'No description available.')
                
                # Split description into max 4 bullets
                bullets = [b.strip() for b in description.split('.') if b.strip()]
                bullets = bullets[:4]
                
                skills.append({
                    'name': name,
                    'bullets': bullets,
                    'path': f"@/{skill_path.absolute()}"
                })
    
    index_content = "# Skills Index (Generated)\n\n"
    index_content += "This file is auto-generated. Do not edit directly.\n\n"
    for skill in skills:
        index_content += f"## {skill['name']}\n"
        for bullet in skill['bullets']:
            index_content += f"- {bullet}\n"
        index_content += f"**Canonical Doc:** {skill['path']}\n\n"
    
    with open(rules_dir / "skills-index.generated.md", 'w') as f:
        f.write(index_content)
    
    print(f"Generated index with {len(skills)} skills.")

if __name__ == "__main__":
    generate_index()
