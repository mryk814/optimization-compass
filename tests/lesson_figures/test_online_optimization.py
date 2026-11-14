from __future__ import annotations

from scripts.lesson_figures.online_optimization import FIGURES


def test_online_optimization_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.online_optimization import ol_alternating, ol_pattern, ol_play

    regrets = {
        days: [
            round(ol_play(seq(days), rule)[1], 2)
            for seq in (ol_alternating, ol_pattern)
            for rule in ("leader", "half", "ogd")
        ]
        for days in (10, 100, 1000, 10000)
    }
    assert regrets[10] == [4.75, 0.25, 1.67, 0.5, 2.0, 1.63]
    assert regrets[100] == [49.75, 0.25, 5.2, 0.5, 17.0, 4.8]
    assert regrets[10000] == [4999.75, 0.25, 50.24, 0.5, 1667.0, 46.08]
    shares, _ = ol_play(ol_alternating(10), "leader")
    assert shares == [0.5, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    days = FIGURES["online-budget-days.svg"]()
    for text in ("媒体A", "勾配で少しずつ"):
        assert text in days
    growth = FIGURES["online-regret-growth.svg"]()
    for text in ("49.75", "17", "5.2", "4.8"):
        assert text in growth
