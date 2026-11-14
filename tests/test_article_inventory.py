from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path

from optimization_compass.content_models import ContentPage, load_content
from optimization_compass.owner_approvals import record_owner_approval
from scripts.article_inventory import inventory_rows, learning_path_targets, render_rows

ROOT = Path(__file__).parents[1]


def _page(content_id: str, body: str) -> ContentPage:
    template = next(page for page in load_content(ROOT / "content") if page.kind == "concept")
    return replace(template, content_id=content_id, body=body, status="published")


def test_rows_put_learning_paths_first_then_articles_without_any_figure(tmp_path: Path) -> None:
    figure = '![図](./media/x.svg "説明")\n'
    explorable = "::: explorable demo-walk\n図です。\n:::\n"
    pages = [
        _page("b.two-visuals", "## 節\n\n本文。\n\n" + figure + explorable),
        _page("c.no-figure", "## 節\n\n本文。"),
        _page("d.one-figure", "## 節\n\n本文。\n\n" + figure),
        _page("a.on-path", "## 節\n\n本文。\n\n" + figure + figure),
        _page("e.draft", "## 節\n\n本文。"),
    ]
    pages[-1] = replace(pages[-1], status="draft")
    record_owner_approval(tmp_path, pages[1], approved_on=date(2026, 11, 14))
    record_owner_approval(tmp_path, pages[2], approved_on=date(2026, 11, 14))
    pages[2] = replace(pages[2], body=pages[2].body + "\n\n追記です。")

    rows = inventory_rows(
        pages,
        path_targets=frozenset({"a.on-path"}),
        beats={"demo-walk": True},
        approvals_root=tmp_path,
    )

    assert [row.content_id for row in rows] == [
        "a.on-path",
        "c.no-figure",
        "d.one-figure",
        "b.two-visuals",
    ]
    by_id = {row.content_id: row for row in rows}
    assert by_id["a.on-path"].static_figures == 2
    assert by_id["b.two-visuals"].explorables_with_beats == ("demo-walk",)
    assert by_id["c.no-figure"].owner == "approved"
    assert by_id["d.one-figure"].owner == "changed"
    assert by_id["b.two-visuals"].owner is None
    assert "owner approved 1 (changed since: 1)" in render_rows(rows)


def test_learning_path_targets_include_formulations_and_articles() -> None:
    targets = learning_path_targets(ROOT)

    assert "PA017" in targets
    assert any(not target.startswith("PA") for target in targets)
