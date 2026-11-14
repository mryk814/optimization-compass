from __future__ import annotations

from scripts.lesson_figures.equilibrium_variational_inequality import FIGURES


def test_equilibrium_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.equilibrium_variational_inequality import (
        EQ_STEPS,
        eq_equilibrium,
        eq_field,
        eq_projection,
    )

    assert [round(v, 3) for v in eq_equilibrium()] == [2.5, 2.167, 1.167]
    assert [round(v, 3) + 0.0 for v in eq_field(eq_equilibrium())] == [-0.667, 0.0, 0.0]
    counts = [len(eq_projection(step)) - 1 for step in EQ_STEPS]
    assert counts == [104, 53, 42, 35, 25, 29, 57, 2000]
    assert [round(v, 1) for v in eq_projection(0.6)[1]] == [2.5, 4.8, 4.2]
    profit = FIGURES["equilibrium-bakery-profit.svg"]()
    for text in ("Aの上限 2.5", "値段 4.17", "値段 6.00", "値段 4.50"):
        assert text in profit
    steps = FIGURES["equilibrium-projection-steps.svg"]()
    for text in ("γ=0.25で42回", "γ=0.6では着かない"):
        assert text in steps
