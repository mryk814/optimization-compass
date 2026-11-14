from __future__ import annotations

from scripts.lesson_figures.robust_parameter_estimation import FIGURES


def test_robust_estimation_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.robust_parameter_estimation import (
        RPE_BAD,
        rpe_huber_profile,
        rpe_irls,
        rpe_residuals,
        rpe_squares_profile,
        rpe_valleys,
        rpe_weights,
    )

    squares = rpe_valleys(rpe_squares_profile)
    assert [(round(w, 2), round(v, 2)) for w, v in squares] == [
        (0.29, 12.83),
        (2.31, 9.2),
        (4.57, 11.83),
        (6.05, 8.3),
    ]
    huber = rpe_valleys(rpe_huber_profile)
    assert [(round(w, 2), round(v, 3)) for w, v in huber] == [
        (2.01, 1.108),
        (3.67, 2.418),
        (4.37, 1.834),
        (5.73, 1.489),
    ]
    rows = rpe_irls()
    table = [
        (1.0, 1.8, 1.866),
        (1.53, 2.087, 1.302),
        (1.821, 2.016, 1.127),
        (1.927, 2.006, 1.109),
        (1.945, 2.006, 1.108),
    ]
    for row, (a, w, loss) in zip(rows, table, strict=False):
        assert (round(row[0], 3), round(row[1], 3), round(row[2], 3)) == (a, w, loss)
    a, w = rows[-1][:2]
    assert (round(a, 3), round(w, 3)) == (1.946, 2.005)
    assert round(rpe_residuals(a, w)[RPE_BAD], 2) == -3.56
    weights = rpe_weights(a, w)
    assert round(weights[RPE_BAD], 3) == 0.084
    assert all(value == 1.0 for i, value in enumerate(weights) if i != RPE_BAD)
    profile = FIGURES["robust-estimation-profile.svg"]()
    for text in ("ω=6.05：8.30", "ω=2.31：9.20", "ω=2.01：1.11"):
        assert text in profile
    weight_figure = FIGURES["robust-estimation-weights.svg"]()
    for text in ("Huber：ω=2.01", "二乗和：ω=6.05", "0.084"):
        assert text in weight_figure
