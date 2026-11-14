from __future__ import annotations

from scripts.lesson_figures.robust_regression import FIGURES


def test_robust_regression_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.robust_regression import robust_fit

    squared_x, squared = robust_fit(None)
    huber_x, huber = robust_fit(1.0)
    assert round(squared_x, 9) == 2.5
    assert [round(value, 9) for value in squared] == [2.5, 2.5, 2.5, -7.5]
    assert round(huber_x, 9) == round(1 / 3, 9)
    assert [round(value, 9) for value in huber] == [round(1 / 3, 9)] * 3 + [-1.0]
    assert abs(sum(squared)) < 1e-9 and abs(sum(huber)) < 1e-9
    assert "Huberの解 x=1/3" in FIGURES["robust-regression-huber.svg"]()
