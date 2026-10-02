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
    style_warnings,
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


def test_language_contract_detects_bare_mixed_prose() -> None:
    page = next(page for page in _published_pages() if page.kind == "concept")
    noisy = replace(page, body="costを最小化し、状態fieldを更新します。")

    warnings = language_contract_warnings(noisy)

    assert [(warning.code, warning.detail) for warning in warnings] == [
        ("prose.language-mixing", "costを"),
        ("prose.language-mixing", "状態field"),
    ]


def _with_body(body: str) -> ContentPage:
    page = next(page for page in _published_pages() if page.kind == "concept")
    return replace(page, body=body)


def _codes(body: str) -> list[str]:
    return [warning.code for warning in style_warnings(_with_body(body))]


def test_work_report_phrases_are_warned() -> None:
    warnings = style_warnings(
        _with_body("数値積分でも同じ値を確かめました。\n\n単位は、この教材のために揃えています。")
    )

    assert [(warning.code, warning.detail) for warning in warnings] == [
        ("prose.work-report", "確かめました"),
        ("prose.work-report", "この教材のため"),
    ]
    assert _codes("係数を回して、頂点が切り替わる瞬間を確かめてください。") == []


def test_overprecise_numbers_are_warned_in_prose_and_tables_only() -> None:
    body = (
        "普通に平均すると 2.500000 です。\n\n"
        "| 方法 | 推定値 |\n|---|---:|\n| 平均 | 2.500000 |\n| Huber | 0.333 |\n\n"
        "式では $x=0.3333333$ と書けます。`print(2.500000)` の出力は 2.5 です。\n\n"
        "```text\n2.500000\n```\n\n$$\nx = 0.3333333\n$$\n"
    )

    warnings = style_warnings(_with_body(body))

    assert [(warning.code, warning.line) for warning in warnings] == [
        ("number.overprecise", 1),
        ("number.overprecise", 5),
    ]
    assert _codes("収束までに 0.1234 秒かかりました。") == []


def test_choppy_runs_of_one_sentence_lines_are_warned() -> None:
    choppy = "\n".join(f"{index}番目の短い文です。" for index in range(6))
    linked = choppy.replace("3番目", "つまり3番目")
    shorter = "\n".join(f"{index}番目の短い文です。" for index in range(5))

    assert _codes(choppy) == ["prose.choppy"]
    assert _codes(linked) == []
    assert _codes(shorter) == []
    assert _codes(choppy.replace("\n3番目", "\n\n3番目")) == []


def test_linear_program_model_article_is_not_choppy() -> None:
    page = next(page for page in _published_pages() if page.content_id == "concept.linear-program")

    assert "prose.choppy" not in {warning.code for warning in style_warnings(page)}


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
