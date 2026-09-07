import re
from pathlib import Path

from cutgen_knowledge.agents import analyst, curator, selector, writer

SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"
AGENTS_DIR = Path(__file__).resolve().parents[1] / "src" / "cutgen_knowledge" / "agents"


def test_all_agent_prompt_paths_resolve():
    for module in (analyst, curator, selector, writer):
        assert module.PROMPT_PATH.exists(), module.PROMPT_PATH
        text = module.PROMPT_PATH.read_text(encoding="utf-8")
        assert text.startswith("---\n")


def test_skills_frontmatter_matches_directory_name():
    for skill_path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_path.read_text(encoding="utf-8")
        match = re.match(r"^---\nname: (\S+)\n", text)
        assert match, f"{skill_path}: sem frontmatter name:"
        assert match.group(1) == skill_path.parent.name
        assert "description:" in text


def test_skills_reference_existing_agent_modules():
    for mod in ("analyst", "curator", "selector", "writer"):
        assert (AGENTS_DIR / f"{mod}.py").exists()
