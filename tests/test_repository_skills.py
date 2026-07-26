from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines and lines[0] == "---", f"{path} must start with YAML frontmatter"
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise AssertionError(f"{path} frontmatter is not closed") from error
    payload = yaml.safe_load("\n".join(lines[1:closing]))
    assert isinstance(payload, dict), f"{path} frontmatter must be a mapping"
    return payload, "\n".join(lines[closing + 1 :]).strip()


def test_repository_skills_have_discoverable_minimal_frontmatter() -> None:
    skill_files = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
    assert skill_files, "repository must expose at least one agent skill"

    names: list[str] = []
    for path in skill_files:
        metadata, body = _frontmatter(path)
        assert set(metadata) == {"name", "description"}
        name = metadata["name"]
        description = metadata["description"]
        assert isinstance(name, str) and SKILL_NAME.fullmatch(name)
        assert name == path.parent.name
        assert len(name) <= 64
        assert isinstance(description, str) and description.strip()
        assert len(description) <= 1024
        assert body.startswith("# "), f"{path} body must start with an H1"
        names.append(name)

    assert len(names) == len(set(names))
