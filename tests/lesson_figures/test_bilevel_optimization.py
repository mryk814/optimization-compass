from __future__ import annotations

from scripts.lesson_figures.bilevel_optimization import FIGURES


def test_bilevel_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.bilevel_optimization import _bilevel_data

    data = _bilevel_data()
    assert (data["best_x"], data["best_y"], data["best_revenue"]) == (2.0, 2.0, 4.0)
    assert (data["assumed_at_max"], data["actual_at_max"]) == (18.0, 0.0)
    xs = data["xs"]
    assert [data["revenue"][xs.index(x)] for x in (0.0, 1.0, 2.0, 3.0, 4.0)] == [
        0.0,
        3.0,
        4.0,
        3.0,
        0.0,
    ]
    figure = FIGURES["bilevel-pricing-response.svg"]()
    assert "x=2 で y=2" in figure and "最大 4" in figure
    assert "stroke-dasharray" not in figure
