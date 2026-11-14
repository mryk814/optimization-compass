from __future__ import annotations

from scripts.lesson_figures.sat_maxsat import FIGURES


def test_sat_maxsat_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.sat_maxsat import (
        sat_feasible,
        sat_greedy,
        sat_implications,
        sat_label,
        sat_weight,
    )

    plans = {sat_label(x): sat_weight(x) for x in sat_feasible()}
    assert plans == {"BD": 0, "BCD": 3, "A": 2, "AE": 4, "AD": 2, "ABD": 2}
    assert sat_label(sat_greedy()) == "BCD"
    assert [lit for lit, _ in sat_implications(3)] == [3, -1, 2, 4, -5]
    assert [reason for _, reason in sat_implications(3)] == ["", "店番A・C", "鍵", "車", "店番D・E"]
    assert [lit for lit, _ in sat_implications(5)] == [5, -4, -2, 1, -3]
    grid = FIGURES["sat-invite-grid.svg"]()
    for text in ("最も重い：AE（4）", "重い順：BCD（3）"):
        assert text in grid
    chain = FIGURES["sat-invite-chain.svg"]()
    for text in ("① Cを呼ぶと", "② Eを呼ぶと", "¬E", "¬C"):
        assert text in chain
