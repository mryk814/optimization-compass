from __future__ import annotations

import math

from scripts.lesson_figures.eigenvalue_problem import FIGURES


def test_eigenvalue_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.eigenvalue_problem import (
        eig_best_angle,
        eig_centre,
        eig_perpendicular_sum,
        eig_scatter,
        eig_values,
    )

    assert eig_centre() == (4.0, 3.0)
    assert eig_scatter() == (4.0, 4.0, 10.0)
    assert eig_values() == (2.0, 12.0)
    assert math.isclose(math.tan(math.radians(eig_best_angle())), 2.0)
    assert math.isclose(eig_perpendicular_sum(eig_best_angle()), 2.0)
    assert math.isclose(eig_perpendicular_sum(45.0), 3.0)
    assert math.isclose(eig_perpendicular_sum(0.0), 10.0)
    # 7 + 3 cos 2φ − 4 sin 2φ, the article's closed form
    for angle in range(0, 180, 15):
        phi = math.radians(angle)
        closed = 7 + 3 * math.cos(2 * phi) - 4 * math.sin(2 * phi)
        assert math.isclose(eig_perpendicular_sum(angle), closed)
    fence = FIGURES["eigenvalue-fence-direction.svg"]()
    for text in ("63.4° で最小 2", "153.4° で最大 12", "45°（縦のずれで当てはめた直線）で 3"):
        assert text in fence
    parallel = FIGURES["eigenvalue-parallel-condition.svg"]()
    for text in ("M n=(4, 4)", "M n=2 n", "n=(2, −1)/√5"):
        assert text in parallel
