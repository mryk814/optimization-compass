from __future__ import annotations

from scripts.lesson_figures.repeated_parametric_optimization import FIGURES


def test_repeated_parametric_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.repeated_parametric_optimization import pq_sequence, pq_solve

    assert [round(v, 3) for v in pq_solve(2.0)[0]] == [1.0, 1.0]
    assert [round(v, 3) for v in pq_solve(4.5)[0]] == [3.0, 1.5]
    assert [round(v, 3) for v in pq_solve(6.5)[0]] == [4.0, 2.5]
    assert [round(pq_solve(t)[1][0], 3) for t in (2.0, 4.5, 6.5)] == [1.0, 3.0, 5.0]
    cold, warm = pq_sequence()
    assert cold == [3, 3, 2, 2, 2, 3, 3, 3, 2, 2, 3, 3]
    assert warm == [3, 1, 2, 1, 1, 2, 1, 1, 2, 1, 2, 3]
    regions = FIGURES["parametric-production-regions.svg"]()
    for text in ("1号機", "2号機の下限", "1号機の上限"):
        assert text in regions
    warm_svg = FIGURES["parametric-warm-start.svg"]()
    for text in ("合計31", "合計20"):
        assert text in warm_svg
