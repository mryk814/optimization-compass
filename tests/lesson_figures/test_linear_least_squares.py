from __future__ import annotations

from scripts.lesson_figures.linear_least_squares import (
    FIGURES,
    least_squares_fit,
    least_squares_sse,
)


def test_least_squares_figures_use_the_article_numbers() -> None:
    x1, x2, sse = least_squares_fit()
    assert (round(x1, 6), round(x2, 6), round(sse, 6)) == (0.9, 0.9, 0.7)
    assert round(least_squares_sse(0.5, 1.3), 6) == 1.66
    figures = {name: draw() for name, draw in FIGURES.items()}
    assert "この直線では合計 0.70" in figures["least-squares-residuals.svg"]
    assert "二乗和 1.66" in figures["least-squares-contours.svg"]
    assert figures["least-squares-minimum.svg"].count("0.9 で最小 0.70") == 2
