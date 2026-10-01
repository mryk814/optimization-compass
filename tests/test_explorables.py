from pathlib import Path

import pytest

from optimization_compass.content_models import load_content, parse_content
from optimization_compass.explorables import load_explorables

_HEADER = """---
content_id: concept.example
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_CONVEXITY
title_ja: Example
title_en: Example
summary: Summary.
source_ids: [S001]
status: draft
last_reviewed: 2026-07-15
---

"""


def _page(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "content/concepts/example.md"
    path.parent.mkdir(parents=True)
    path.write_text(_HEADER + body, encoding="utf-8")
    return path


def test_registry_entries_state_question_and_limits() -> None:
    registry = load_explorables()

    assert {"gradient-descent-valley", "lp-vertex-walk", "convexity-chord"} <= set(registry)
    for entry in registry.values():
        assert entry.question.endswith("。")
        assert entry.not_implied.endswith("。")


def test_explorable_block_compiles_to_mount_point_with_visible_caption(tmp_path: Path) -> None:
    path = _page(
        tmp_path,
        "## Overview\n\nSummary.\n\n"
        "::: explorable convexity-chord\n"
        "点を動かして、線分とグラフの上下を確かめます。\n"
        ":::\n\n"
        "## After\n\nText.\n",
    )

    page = parse_content(path)

    assert 'data-explorable-id="convexity-chord"' in page.html
    assert "data-explorable-mount" in page.html
    assert '<figcaption class="explorable-caption"><p>点を動かして' in page.html
    assert "</p>\n</figcaption></figure>" in page.html
    assert [heading.label for heading in page.toc] == ["Overview", "After"]


@pytest.mark.parametrize(
    ("block", "message"),
    [
        ("::: explorable no-such-figure\nCaption.\n:::", "unknown explorable id"),
        ("::: explorable\nCaption.\n:::", "exactly one kebab-case id"),
        ("::: explorable Bad_Id\nCaption.\n:::", "exactly one kebab-case id"),
        ("::: explorable convexity-chord\n:::", "exactly one caption paragraph"),
        (
            "::: explorable convexity-chord\nOne.\n\nTwo.\n:::",
            "exactly one caption paragraph",
        ),
        (
            "::: explorable convexity-chord\n- item\n:::",
            "exactly one caption paragraph",
        ),
        (
            '::: explorable convexity-chord\n![a](https://example.com/a.png "c")\n:::',
            "caption must be text",
        ),
        (
            "::: explorable convexity-chord\nA.\n:::\n\n::: explorable convexity-chord\nB.\n:::",
            "used more than once",
        ),
        (
            "- item\n\n  ::: explorable convexity-chord\n  Caption.\n  :::",
            "top-level block",
        ),
    ],
)
def test_explorable_block_rejects_invalid_authoring(
    tmp_path: Path, block: str, message: str
) -> None:
    path = _page(tmp_path, f"## Overview\n\nSummary.\n\n{block}\n")

    with pytest.raises(ValueError, match=message):
        parse_content(path)


def test_published_articles_only_use_registered_explorables() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = set(load_explorables())
    used: set[str] = set()

    for page in load_content(root / "content"):
        for line in page.body.splitlines():
            if line.startswith("::: explorable "):
                used.add(line.split()[2])

    assert used <= registry
    assert used, "at least one article should embed an explorable"
