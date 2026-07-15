import re
from pathlib import Path

import pytest

from optimization_compass.content_models import load_content, parse_content


def test_published_content_pages_compile_to_safe_accessible_html() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = load_content(root / "content")
    page_ids = {page.content_id for page in pages}

    assert len(pages) >= 12
    assert {
        "concept.convexity",
        "concept.derivative-free",
        "method.gradient-descent",
        "method.nelder-mead",
        "branch-and-bound",
        "bayesian-optimization",
        "cp-sat",
        "least-squares",
        "lp-qp-conic",
        "constrained-continuous",
        "multi-objective",
        "cma-es",
    } <= page_ids
    assert len(page_ids) == len(pages)
    assert all(page.html and page.toc for page in pages)
    assert all(page.source_ids for page in pages)
    combined = "\n".join(page.html for page in pages)
    assert "<math" in combined
    assert 'class="language-python"' in combined
    assert "<table>" in combined
    assert "<ol>" in combined
    assert "<ul>" in combined
    assert 'class="callout callout-warning"' in combined
    assert "<figure>" in combined
    assert 'rel="noopener noreferrer"' in combined
    assert "<script" not in combined


def test_promoted_method_pages_have_syntax_valid_copyable_examples() -> None:
    root = Path(__file__).resolve().parents[1]
    promoted_ids = {
        "cp-sat",
        "least-squares",
        "lp-qp-conic",
        "constrained-continuous",
        "multi-objective",
        "cma-es",
    }
    pages = {page.content_id: page for page in load_content(root / "content")}

    for content_id in promoted_ids:
        blocks = re.findall(
            r"^```python\n(.*?)^```$", pages[content_id].body, re.MULTILINE | re.DOTALL
        )
        assert blocks, f"{content_id} must provide a copyable Python example"
        for index, block in enumerate(blocks, start=1):
            compile(block, f"{content_id}:python:{index}", "exec")


def test_markdown_pipeline_compiles_supported_constructs(tmp_path: Path) -> None:
    path = _write_page(
        tmp_path,
        """## Overview

Summary.

### Details

- item with `code`
- [source](https://example.com/reference)

| Name | Value |
| --- | --- |
| alpha | $\\alpha$ |

::: note
Check this.
:::

```python
print("safe")
```

![curve](./media/curve.svg "Convex curve")
""",
    )
    asset = tmp_path / "site/public/media/curve.svg"
    asset.parent.mkdir(parents=True)
    asset.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")

    page = parse_content(path)

    assert [heading.level for heading in page.toc] == [2, 3]
    assert (
        '<a href="https://example.com/reference" target="_blank" rel="noopener noreferrer">'
        in page.html
    )
    assert '<img src="./media/curve.svg" alt="curve" loading="lazy">' in page.html
    assert "<figcaption>Convex curve</figcaption>" in page.html
    assert "<math" in page.html


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("## Safe\n\nSummary.\n\n<script>alert(1)</script>", "raw HTML is forbidden"),
        ("## Safe\n\nSummary with [bad](javascript:alert(1)).", "URL must be an HTTPS URL"),
        ("## Safe\n\nSummary.\n\n[missing](#unknown)", "unknown heading"),
        ("## Safe\n\nSummary.\n\n#### Skipped", "heading hierarchy skips"),
        ("## Safe\n\nSummary.\n\n```ruby\nputs 1\n```", "unsupported fenced code language"),
        ("## Safe\n\nSummary.\n\n```python\nprint(1)", "fenced code block is not closed"),
        ("## Safe\n\nSummary.\n\n![alt](https://example.com/a.png)", "title caption"),
        (
            '## Safe\n\nSummary.\n\nText ![alt](https://example.com/a.png "caption") inline.',
            "figures must be placed on their own line",
        ),
    ],
)
def test_markdown_pipeline_rejects_unsafe_or_broken_constructs(
    tmp_path: Path, body: str, message: str
) -> None:
    path = _write_page(tmp_path, body)

    with pytest.raises(ValueError, match=message):
        parse_content(path)


def test_frontmatter_is_strict_yaml_schema(tmp_path: Path) -> None:
    path = _write_page(tmp_path, "## Safe\n\nSummary.", extra="unknown_field: nope\n")

    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        parse_content(path)


def test_frontmatter_summary_must_match_body(tmp_path: Path) -> None:
    path = _write_page(tmp_path, "## Safe\n\nDifferent.")

    with pytest.raises(ValueError, match="summary must match"):
        parse_content(path)


def _write_page(tmp_path: Path, body: str, *, extra: str = "") -> Path:
    path = tmp_path / "content/concepts/example.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        """---
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
"""
        + extra
        + "---\n\n"
        + body,
        encoding="utf-8",
    )
    return path
