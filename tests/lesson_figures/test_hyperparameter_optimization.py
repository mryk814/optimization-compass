from __future__ import annotations

import math

from scripts.lesson_figures.hyperparameter_optimization import FIGURES, hpo_search_data


def test_hpo_search_figure_uses_the_article_numbers() -> None:
    data = hpo_search_data()
    grid, rand = data["grid"], data["random"]
    assert (grid["distinct_lam"], grid["distinct_degree"]) == (4, 4)
    assert (rand["distinct_lam"], rand["distinct_degree"]) == (16, 11)
    grid_d, grid_lam = grid["configs"][grid["best"]]
    rand_d, rand_lam = rand["configs"][rand["best"]]
    assert round(grid["values"][grid["best"]], 3) == 0.192
    assert (grid_d, round(math.log10(grid_lam), 2)) == (6, -3.67)
    assert round(rand["values"][rand["best"]], 3) == 0.144
    assert (rand_d, round(math.log10(rand_lam), 2)) == (3, -1.67)
    assert round(data["terrain"][(3, 2)], 3) == 0.137  # degree 3 at log10 lambda = -4.75
    figure = FIGURES["hpo-search-points.svg"]()
    assert "格子ではlog10 λの値が4種類、ランダムでは16種類" in figure
    assert "格子が0.192、ランダムが0.144" in figure
    assert "stroke-dasharray" not in figure
