from __future__ import annotations

import math

from scripts.lesson_figures.nonsmooth_convex_composite import (
    FIGURES,
    composite_objective,
    composite_solution,
    composite_step,
)


def test_composite_group_figure_uses_the_article_numbers() -> None:
    v, moved = composite_step([0.0] * 4)
    assert [round(value, 4) for value in v] == [0.85, 0.55, 0.3, 0.25]
    assert [round(value, 4) for value in moved] == [0.4722, 0.3055, 0.0, 0.0]
    assert round(math.hypot(v[0], v[1]), 3) == 1.012
    assert round(math.hypot(v[2], v[3]), 3) == 0.391
    x, count = composite_solution()
    assert count == 34
    assert [round(value, 4) for value in x] == [0.8145, 0.5026, 0.0, 0.0]
    assert round(composite_objective(x), 4) == 12.1193
    assert round(composite_objective([0.0] * 4), 1) == 17.5
    figure = FIGURES["composite-group-shrink.svg"]()
    for text in (
        "(0.85, 0.55)",
        "長さ 1.012 &gt; 0.45",
        "→ (0.472, 0.306)",
        "→ (0, 0)",
        "長さ 0.391 ≤ 0.45",
    ):
        assert text in figure
