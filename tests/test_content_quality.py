from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from optimization_compass.content_models import ContentPage, load_content
from optimization_compass.content_quality import (
    inspect_concept,
    language_contract_warnings,
    public_content_routes,
    require_published_concept_quality,
)
from optimization_compass.formulation_atlas import authored_route_ids


def _published_pages() -> list[ContentPage]:
    root = Path(__file__).parents[1]
    return [page for page in load_content(root / "content") if page.status == "published"]


def _public_routes(pages: list[ContentPage]) -> frozenset[str]:
    root = Path(__file__).parents[1]
    gallery = json.loads((root / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    comparisons = json.loads(
        (root / "data/seeds/site_comparisons.json").read_text(encoding="utf-8")
    )
    formulation_ids, path_ids = authored_route_ids(root)
    return public_content_routes(
        pages,
        gallery_ids=(item["case_id"] for item in gallery["cases"]),
        comparison_ids=(item["comparison_id"] for item in comparisons["comparisons"]),
        formulation_ids=formulation_ids,
        path_ids=path_ids,
    )


def test_all_published_concepts_meet_the_publication_floor() -> None:
    pages = _published_pages()
    routes = _public_routes(pages)

    rows = require_published_concept_quality(pages, routes)

    assert rows
    assert all(row.meets_floor for row in rows)


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


def test_language_contract_detects_bare_mixed_prose() -> None:
    page = next(page for page in _published_pages() if page.kind == "concept")
    noisy = replace(page, body="costを最小化し、状態fieldを更新します。")

    warnings = language_contract_warnings(noisy)

    assert [(warning.code, warning.detail) for warning in warnings] == [
        ("prose.language-mixing", "costを"),
        ("prose.language-mixing", "状態field"),
    ]


def test_learner_first_article_keeps_next_route_validation() -> None:
    pages = _published_pages()
    page = next(page for page in pages if page.content_id == "concept.linear-least-squares")
    routes = _public_routes(pages)
    assert inspect_concept(page, routes).meets_floor
    broken = replace(
        page,
        body=page.body.replace("#/formulations/PA035", "#/learn/missing-concept"),
    )
    assert inspect_concept(broken, routes).invalid_next_links == ("#/learn/missing-concept",)
