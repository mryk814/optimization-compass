from __future__ import annotations

import math

from scripts.lesson_figures.robust_optimization import FIGURES


def test_robust_optimization_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.robust_optimization import (
        ro_coefficients,
        ro_content,
        ro_shortfall_probability,
        ro_solve,
        ro_switch,
    )

    nominal, nominal_cost = ro_solve(0.0)
    robust, robust_cost = ro_solve(1.0)
    assert [round(v, 9) for v in nominal] == [2.0, 6.0]
    assert math.isclose(nominal_cost, 13.2)
    assert math.isclose(robust[0], 50 / 9) and robust[1] == 0.0
    assert math.isclose(robust_cost, 50 / 3)
    assert math.isclose(ro_content(nominal, ro_coefficients(1.0)), 6.6)
    assert math.isclose(ro_shortfall_probability(nominal), 0.5)
    assert ro_shortfall_probability(robust) == 0.0
    # The table: k, cost, smallest nitrogen over the recorded box, shortfall percentage
    rows = {0.25: (14.62, 7.63, 34.8), 0.45: (15.63, 8.35, 21.0), 0.5: (15.79, 9.47, 25.0)}
    for k, (cost, nitrogen, percent) in rows.items():
        x, value = ro_solve(k)
        assert round(value, 2) == cost
        assert round(ro_content(x, ro_coefficients(1.0)), 2) == nitrogen
        assert round(100 * ro_shortfall_probability(x), 1) == percent
    assert math.isclose(ro_switch(), 10 / 21, rel_tol=1e-9)
    box = FIGURES["robust-optimization-box.svg"]()
    for text in ("(2, 6)：13.2千円", "橙の点 (5.56, 0)", "16.67千円", "少ない角 (1.8, 0.5)"):
        assert text in box
    size = FIGURES["robust-optimization-set-size.svg"]()
    for text in ("k=0.476", "50%", "21%", "25%", "15.75", "16.67"):
        assert text in size
