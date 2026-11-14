from __future__ import annotations

from scripts.lesson_figures.l1_sparse_regularization import (
    FIGURES,
    lasso_lambda_max,
    lasso_solution,
    lasso_zero_points,
    ridge_solution,
)


def test_l1_path_figure_uses_the_article_numbers() -> None:
    assert round(lasso_lambda_max(), 2) == 18.96
    assert [round(value, 1) for value in lasso_zero_points()] == [19.0, 12.6, 7.2, 4.8]
    assert [round(value, 2) for value in lasso_solution(10.0)] == [0.74, -0.21, 0.0, 0.0]
    assert [round(value, 2) for value in lasso_solution(0.0)] == [1.77, -1.18, -0.9, 0.21]
    assert [round(value, 2) for value in ridge_solution(10.0)] == [0.88, -0.61, -0.29, 0.25]
    assert all(value != 0.0 for value in ridge_solution(20.0))
    figure = FIGURES["l1-sparse-regularization-path.svg"]()
    assert "階数は4.8、徒歩は7.2、築年数は12.6、面積は19.0で0になります" in figure
    assert "stroke-dasharray" not in figure
