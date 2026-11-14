from __future__ import annotations

from scripts.lesson_figures.stochastic_programming import FIGURES


def test_stochastic_programming_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.stochastic_programming import (
        sp_best,
        sp_cost,
        sp_expected,
        sp_mean_demand,
    )

    assert sp_best() == (40, 7000.0)
    assert sp_mean_demand() == 46.0
    assert [sp_expected(x) for x in (0, 20, 40, 46, 80)] == [11500, 8500, 7000, 7150, 8000]
    assert [sp_cost(40, d) for d in (20, 40, 80)] == [4000, 4000, 14000]
    cost = FIGURES["stochastic-programming-expected-cost.svg"]()
    for text in ("x=40：7000", "x=46：7150", "x=80：8000", "晴れ 80個"):
        assert text in cost
    tree = FIGURES["stochastic-programming-two-stage.svg"]()
    for text in ("x=40", "取り寄せ y=0", "取り寄せ y=40"):
        assert text in tree
