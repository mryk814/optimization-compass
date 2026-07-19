from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from optimization_compass.content_models import ContentPage, load_content
from optimization_compass.content_quality import (
    inspect_concept,
    public_content_routes,
    render_content_quality_report,
    require_published_concept_quality,
    style_warnings,
)


def _published_pages() -> list[ContentPage]:
    root = Path(__file__).parents[1]
    return [page for page in load_content(root / "content") if page.status == "published"]


def _public_routes(pages: list[ContentPage]) -> frozenset[str]:
    root = Path(__file__).parents[1]
    gallery = json.loads((root / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    comparisons = json.loads(
        (root / "data/seeds/site_comparisons.json").read_text(encoding="utf-8")
    )
    return public_content_routes(
        pages,
        gallery_ids=(item["case_id"] for item in gallery["cases"]),
        comparison_ids=(item["comparison_id"] for item in comparisons["comparisons"]),
    )


def test_all_published_concepts_meet_the_publication_floor() -> None:
    pages = _published_pages()
    routes = _public_routes(pages)

    rows = require_published_concept_quality(pages, routes)

    assert rows
    assert all(row.meets_floor for row in rows)


def test_committed_quality_report_matches_canonical_content() -> None:
    root = Path(__file__).parents[1]
    pages = _published_pages()
    routes = _public_routes(pages)
    rows = [inspect_concept(page, routes) for page in pages if page.kind == "concept"]

    expected = render_content_quality_report(rows, load_content(root / "content"))
    committed = (root / "docs/content-quality-report.md").read_text(encoding="utf-8")

    assert committed == expected


def test_concept_floor_requires_a_valid_next_route() -> None:
    page = next(page for page in _published_pages() if page.content_id == "concept.derivative-free")
    routes = _public_routes(_published_pages())
    incomplete = replace(
        page,
        body=page.body.replace("## 次に読む", "## 関連項目"),
    )

    row = inspect_concept(incomplete, routes)

    assert not row.meets_floor
    assert not row.valid_next_links


def test_unknown_next_route_is_reported_and_rejected() -> None:
    page = next(page for page in _published_pages() if page.content_id == "concept.derivative-free")
    routes = _public_routes(_published_pages())
    broken = replace(
        page,
        body=page.body.replace("#/learn/family.local-dfo", "#/learn/missing-concept"),
    )

    row = inspect_concept(broken, routes)

    assert row.invalid_next_links == ("#/learn/missing-concept",)
    with pytest.raises(ValueError, match="invalid=#/learn/missing-concept"):
        require_published_concept_quality([broken], routes)


def test_draft_content_is_not_a_valid_public_next_route() -> None:
    published = _published_pages()
    draft = replace(published[0], status="draft")

    routes = public_content_routes([draft])

    assert f"#/learn/{draft.content_id}" not in routes


def test_style_warnings_are_review_signals() -> None:
    page = next(page for page in _published_pages() if page.kind == "concept")
    noisy = replace(
        page,
        body=(
            "## Python例\n\n"
            "本稿では、長い説明を、複数の節へ分けず、そのまま一つの文として記述することで、"
            "読み手が一度に保持しなければならない情報を意図的に増やし、"
            "文章の警告を確実に検出できるだけの長さへ調整しています。"
        ),
    )

    codes = {warning.code for warning in style_warnings(noisy)}

    assert codes == {
        "heading.noncanonical",
        "prose.meta",
        "sentence.commas",
        "sentence.long",
    }
