from __future__ import annotations

from scripts.lesson_figures.second_order_cone_program import FIGURES, socp_center


def test_socp_relay_figure_uses_the_article_numbers() -> None:
    from fractions import Fraction

    centre, weights = socp_center()
    assert centre == (Fraction(3), Fraction(1))
    assert weights == (Fraction(1, 3), Fraction(5, 12), Fraction(1, 4))
    # All three villages are at distance sqrt(10) from the centre, and the weights are positive.
    for vx, vy in ((0, 0), (6, 0), (2, 4)):
        assert (vx - 3) ** 2 + (vy - 1) ** 2 == 10
    figure = FIGURES["socp-relay-station.svg"]()
    for text in ("半径 3.6 km", "3.162 km", "Bまで 3.590 km", "(3, 1)", "5/12", "1/4", "1/3"):
        assert text in figure
