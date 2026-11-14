from __future__ import annotations

from scripts.lesson_figures.stochastic_erm import FIGURES


def test_stochastic_erm_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.stochastic_erm import erm_minibatch_data

    data = erm_minibatch_data()
    w0, w1 = data["minimiser"]
    assert (round(w0, 3), round(w1, 3)) == (-0.832, 1.678)
    start, minimum = data["start"], data["minimum"]
    assert [round(value, 4) for value in start["full"]] == [0.1446, -0.2802]
    assert (round(start["rms"], 3), start["same"]) == (0.114, 200)
    assert round(minimum["rms"], 3) == 0.083
    figure = FIGURES["stochastic-erm-minibatch.svg"]()
    assert "200本のうち200本が灰の線の同じ側" in figure
    assert "32件の勾配はRMS 0.083" in figure
    assert "stroke-dasharray" not in figure
