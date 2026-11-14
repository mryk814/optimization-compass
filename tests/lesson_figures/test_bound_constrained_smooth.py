from __future__ import annotations

from scripts.lesson_figures.bound_constrained_smooth import (
    FIGURES,
    box_gradient,
    box_solution,
    box_unconstrained_minimum,
    box_value,
)


def test_bound_constrained_box_figure_uses_the_article_numbers() -> None:
    free = box_unconstrained_minimum()
    assert (free, box_value(*free)) == ((2.0, 0.0), 2.0)
    assert box_value(1.0, 0.0) == 3.0
    x1, x2 = box_solution()
    assert (round(x1, 6), round(x2, 6), round(box_value(x1, x2), 6)) == (1.0, 0.5, 2.5)
    assert tuple(round(g, 6) for g in box_gradient(x1, x2)) == (-1.0, 0.0)
    figure = FIGURES["bound-constrained-box.svg"]()
    for text in ("(1, 0.5)", "f = 2.5", "f = 3", "f = 2"):
        assert text in figure
