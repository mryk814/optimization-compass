from __future__ import annotations

from scripts.lesson_figures.noisy_black_box import FIGURES


def test_noisy_black_box_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.noisy_black_box import (
        oven_figure_data,
        oven_reversal,
        oven_spread,
        oven_true_score,
    )

    once, five = oven_figure_data()
    assert (once["k"], once["n"], five["k"], five["n"]) == (60, 1, 12, 5)
    assert round(once["xs"][once["best"]], 3) == 0.508
    assert round(once["means"][once["best"]], 3) == -0.38
    assert round(once["true_at_best"], 3) == 0.017
    assert round(five["xs"][five["best"]], 3) == 0.625
    assert round(five["means"][five["best"]], 3) == -0.077
    assert round(five["true_at_best"], 3) == 0.001
    # The true score is never negative, so a reported -0.380 cannot be real.
    assert min(oven_true_score(i / 100) for i in range(101)) == 0.0
    # Probability that n-bake means order two temperatures the wrong way round.
    assert [round(oven_reversal(n, 0.02), 3) for n in (1, 5)] == [0.472, 0.437]
    assert [round(oven_reversal(n, 0.08), 3) for n in (1, 5)] == [0.389, 0.264]
    assert [round(oven_reversal(n, 0.32), 3) for n in (1, 5)] == [0.129, 0.006]
    # Repeating the whole procedure 2000 times: the reported minimum is optimistic.
    for k, chosen, optimism in ((60, 0.041, -0.422), (12, 0.025, -0.109), (4, 0.010, -0.013)):
        got_chosen, got_optimism = oven_spread(k)
        assert (round(got_chosen, 3), round(got_optimism, 3)) == (chosen, optimism)
    figure = FIGURES["noisy-black-box-budget.svg"]()
    for text in ("① 60温度を1回ずつ", "② 12温度を5回ずつ", "最良の観測 −0.380、真の点数 0.017"):
        assert text in figure
    assert "最良の平均 −0.077、真の点数 0.001" in figure
    assert "stroke-dasharray" not in figure
