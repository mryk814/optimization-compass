from __future__ import annotations

import math

from scripts.lesson_figures.so3_rotation_representation import FIGURES, so2_points


def test_so2_circle_figure_uses_the_article_numbers() -> None:
    shown = so2_points(1.0)
    # I + J sits on the tangent line with determinant 1 + θ²; exp(J) stays on the circle.
    assert (shown["line_a"], shown["line_b"], shown["line_det"]) == (1.0, 1.0, 2.0)
    assert (round(shown["exp_a"], 3), round(shown["exp_b"], 3)) == (0.54, 0.841)
    assert math.isclose(shown["exp_det"], 1.0)
    gaps = {
        theta: math.hypot(p["line_a"] - p["exp_a"], p["line_b"] - p["exp_b"])
        for theta, p in ((t, so2_points(t)) for t in (0.1, 0.5, 1.0))
    }
    assert [round(gaps[t], 3) for t in (0.1, 0.5, 1.0)] == [0.005, 0.124, 0.486]
    figure = FIGURES["so3-lie-algebra-circle.svg"]()
    for text in ("θ=1：I+J は行列式 2、exp(J) は弧の長さ 1", "接線 θJ", "exp(J)"):
        assert text in figure
