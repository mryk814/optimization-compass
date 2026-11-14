from __future__ import annotations

from scripts.lesson_figures.inverse_problem import FIGURES, inverse_problem_curve


def test_inverse_problem_figure_uses_the_article_numbers() -> None:
    alpha, error, curve = inverse_problem_curve()
    assert f"{alpha:.2e}" == "7.25e-04"
    assert round(error, 4) == 0.0199
    by_exponent = dict(curve)
    assert round(by_exponent[-10.0], 1) == 43.9
    assert round(by_exponent[-3.0], 4) == 0.0182
    assert round(by_exponent[0.0], 2) == 0.61
    assert "α=7.25e-04" in FIGURES["inverse-problem-alpha.svg"]()
