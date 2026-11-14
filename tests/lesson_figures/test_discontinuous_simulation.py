from __future__ import annotations

from scripts.lesson_figures.discontinuous_simulation import FIGURES, dryer_compass, dryer_value


def test_discontinuous_dryer_figure_uses_the_article_numbers() -> None:
    assert dryer_value(0.55) == 0.325
    assert round(0.40 + 2.0 * (0.55 - 0.25) ** 2, 6) == 0.58
    assert (round(dryer_value(0.25), 6), round(dryer_value(0.80), 6)) == (0.4, 0.2)
    assert round(dryer_value(0.10), 6) == 0.445
    assert dryer_value(0.3) == dryer_value(0.3)
    left = dryer_compass(0.10, 0.4)
    right = dryer_compass(0.10, 0.5)
    assert (round(left[0], 3), round(left[1], 3), left[2]) == (0.25, 0.4, 27)
    assert (round(right[0], 3), round(right[1], 3), right[2]) == (0.8, 0.2, 35)
    figure = FIGURES["discontinuous-dryer-cliff.svg"]()
    for text in ("F(0.55) = 0.325", "0.58", "F = 0.445", "F = 0.4", "F = 0.2", "段差 −0.255"):
        assert text in figure
