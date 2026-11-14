from __future__ import annotations

from scripts.lesson_figures.mixed_integer_nonlinear_program import (
    FIGURES,
    minlp_interval_min,
    minlp_value,
)


def test_minlp_figure_uses_the_article_numbers() -> None:
    values = {n: round(minlp_value(n), 2) for n in range(1, 7)}
    assert values == {1: -7.44, 2: -14.88, 3: -22.32, 4: -29.76, 5: -30.0, 6: -27.33}
    relaxed_n, relaxed_value = minlp_interval_min(1.0, 6.0)
    assert round(relaxed_n, 3) == 4.167 and round(relaxed_value, 6) == -31.0
    assert round(relaxed_n) == 4 and min(values, key=values.get) == 5
    left_n, left_value = minlp_interval_min(1.0, 4.0)
    right_n, right_value = minlp_interval_min(5.0, 6.0)
    assert (round(left_n, 6), round(left_value, 2)) == (4.0, -29.76)
    assert (round(right_n, 6), round(right_value, 2)) == (5.0, -30.0)
    figure = FIGURES["minlp-relaxation-branch.svg"]()
    for text in (
        "緩和の最小：n=4.17、値 −31.0",
        "丸めた n=4：値 −29.76",
        "n≤4 の節点：n=4、値 −29.76",
        "n≥5 の節点：n=5、値 −30.0",
    ):
        assert text in figure
    assert "stroke-dasharray" not in figure
