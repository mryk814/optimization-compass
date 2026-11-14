from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from optimization_compass.content_markdown import unrenderable_math
from optimization_compass.content_models import ContentPage, load_content
from optimization_compass.content_quality import (
    broken_internal_links,
    internal_links,
    known_public_routes,
    language_contract_warnings,
    public_content_routes,
    require_internal_links,
    require_renderable_math,
)

ROOT = Path(__file__).parents[1]


def _published_pages() -> list[ContentPage]:
    return [page for page in load_content(ROOT / "content") if page.status == "published"]


def _linking_to(*targets: str) -> ContentPage:
    page = next(page for page in _published_pages() if page.content_id == "concept.derivative-free")
    anchors = "".join(f'<a href="{target}">先</a>' for target in targets)
    return replace(page, html=f"<p>{anchors}</p>")


def test_published_articles_link_only_to_pages_the_site_can_show() -> None:
    pages = _published_pages()

    require_internal_links(pages, known_public_routes(ROOT, pages))

    assert any(internal_links(page) for page in pages)


def test_a_link_to_a_missing_page_is_rejected() -> None:
    routes = known_public_routes(ROOT, _published_pages())
    broken = _linking_to("#/learn/concept.convexity", "#/learn/missing-concept")

    assert broken_internal_links(broken, routes) == ("#/learn/missing-concept",)
    with pytest.raises(ValueError, match=r"concept\.derivative-free \(#/learn/missing-concept\)"):
        require_internal_links([broken], routes)
    require_internal_links([replace(broken, status="draft")], routes)


def test_theater_learning_routes_open_only_learning_slice_scenarios() -> None:
    # Regression: 26 links sent readers to /theater/learning/ for trace scenarios and three to
    # method IDs that do not exist; the site showed "not found" for all of them.
    routes = known_public_routes(ROOT, _published_pages())

    assert "#/theater/learning/SCENARIO_CONSTRAINED_DISK" in routes
    assert "#/theater/learning/SCENARIO_ADAM_QUADRATIC_DIVERGENCE" not in routes
    assert "#/traces/adam-quadratic-divergence" in routes
    assert "#/theater/search-tree/binary-knapsack-bnb-complete" in routes
    assert "#/theater/physical/drone" in routes
    assert "#/methods/M_SMAC_RF" in routes
    assert "#/methods/M_SMAC" not in routes


def test_a_query_string_does_not_change_the_route() -> None:
    routes = known_public_routes(ROOT, _published_pages())

    assert (
        broken_internal_links(_linking_to("#/learn/topology-optimization?figure=arm"), routes) == ()
    )


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


def _math(tex: str) -> str:
    return f"## 式\n\n本文です。\n\n$$\n{tex}\n$$\n"


def test_formulas_whose_rows_would_run_together_are_found() -> None:
    # Regression: three articles used `aligned`, which the site printed on one line with raw `&`.
    assert unrenderable_math(_math(r"\begin{aligned} a &= b \\ c &= d \end{aligned}"))
    assert unrenderable_math(_math(r"a = b \\ c = d"))
    assert unrenderable_math("## 式\n\n行内の $a \\\\ b$ も同じです。\n")
    for renderable in (
        r"\begin{array}{rl} a &= b \\ c &= d \end{array}",
        r"\begin{cases} 1 & x>0 \\ 0 & x\le 0 \end{cases}",
        r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}",
        r"x \& y",
    ):
        assert unrenderable_math(_math(renderable)) == (), renderable
    assert unrenderable_math("## 式\n\n```text\n$$\na \\\\ b\n$$\n```\n") == ()


def test_published_articles_render_every_formula() -> None:
    pages = _published_pages()
    require_renderable_math(pages)

    page = next(page for page in pages if page.content_id == "concept.derivative-free")
    broken = replace(page, body=_math(r"\begin{aligned} a &= b \\ c &= d \end{aligned}"))
    with pytest.raises(ValueError, match=r"concept\.derivative-free"):
        require_renderable_math([broken])
    require_renderable_math([replace(broken, status="draft")])
