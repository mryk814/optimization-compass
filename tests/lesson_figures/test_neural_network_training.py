from __future__ import annotations

from scripts.lesson_figures.neural_network_training import FIGURES


def test_neural_network_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.neural_network_training import (
        NN_START_A,
        NN_START_B,
        nn_gradient,
        nn_loss,
        nn_minimum,
        nn_path,
    )

    wu, wv = nn_minimum()
    assert (round(wu, 4), round(wv, 4)) == (0.7041, 1.0709)
    assert round(nn_loss(wu, wv), 6) == 0.0025
    assert round(nn_loss(0.0, 0.0), 6) == 0.665
    assert nn_gradient(0.0, 0.0) == (0.0, 0.0)
    assert round(nn_loss(*NN_START_A), 4) == 0.8124
    first = nn_path(NN_START_A, 1)[1]
    assert (round(first[0], 4), round(first[1], 4)) == (0.0847, 0.1871)
    assert nn_path(NN_START_A, 400)[-1][0] > 0 > nn_path(NN_START_B, 400)[-1][0]
    figure = FIGURES["nn-training-two-valleys.svg"]()
    for text in ("中点 0.665", "両端の損失 0.0025", "w*=(0.70, 1.07)"):
        assert text in figure
