from __future__ import annotations

from scripts.lesson_figures.mixed_integer_quadratic_program import (
    FIGURES,
    miqp_big_m_rows,
    miqp_enumerate,
    miqp_relaxation,
)


def test_miqp_figure_uses_the_article_numbers() -> None:
    found = miqp_enumerate()
    assert len(found) == 10
    total, subset, weights = found[0]
    assert (round(total, 2), subset) == (120.75, (0, 3, 4))
    assert [round(value, 3) for value in weights] == [0.55, 0.252, 0.198]
    assert [
        (round(value, 2), "".join("ABCDE"[i] for i in sub)) for value, sub, _ in found[1:3]
    ] == [
        (125.73, "ACE"),
        (129.75, "ACD"),
    ]
    by_subset = {sub: round(value, 2) for value, sub, _ in found}
    assert by_subset[(0, 4)] == 146.0  # A=0.6, E=0.4: 36 + 100 + 2 * 5
    bounds = {label: round(bound, 2) for label, bound, _, _ in miqp_big_m_rows()}
    assert list(bounds.values()) == [102.41, 97.09, 92.59, 92.14, 104.59]
    value, weights = miqp_relaxation((1.0,) * 5)
    assert round(value, 2) == 97.09 and round(sum(weights), 6) == 1.0
    assert round(miqp_big_m_rows()[-1][2], 2) == 125.78
    figure = FIGURES["miqp-big-m-bound.svg"]()
    assert "M ＝ 100では下界92.14、最適値120.75" in figure
    assert "stroke-dasharray" not in figure
