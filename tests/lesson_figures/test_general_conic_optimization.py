from __future__ import annotations

from scripts.lesson_figures.general_conic_optimization import FIGURES


def test_general_conic_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.general_conic_optimization import (
        cn_blocks,
        cn_effect,
        cn_multipliers,
        cn_solve,
    )

    x = cn_solve()
    assert [round(v, 3) for v in x] == [3.018, 2.081, 0.901]
    assert round(cn_effect(x), 3) == 7.065
    assert [round(v, 3) for v in cn_multipliers(x)] == [0.641, 0.156]
    assert round(cn_effect(cn_solve(budget=7.0)), 3) == 7.671
    assert round(cn_effect(cn_solve(spread=2.0)), 3) == 7.113
    assert sum(len(values) for _, values, _ in cn_blocks()) == 17
    allocation = FIGURES["conic-promo-allocation.svg"]()
    for text in ("効果 7.07", "効果 7.11", "効果 4.16"):
        assert text in allocation
    assert "長さ 1.50 ≦ 1.5" in FIGURES["conic-blocks.svg"]()
