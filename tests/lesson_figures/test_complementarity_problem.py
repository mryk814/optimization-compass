from __future__ import annotations

from scripts.lesson_figures.complementarity_problem import FIGURES, lcp_contact_data


def test_lcp_active_set_figure_uses_the_article_numbers() -> None:
    from fractions import Fraction

    rows = lcp_contact_data()
    assert [row["active"] for row in rows] == [(), (0,), (1,), (0, 1)]
    assert [row["ok"] for row in rows] == [False, False, False, True]
    assert rows[1]["z"] == [Fraction(1, 2), 0] and rows[1]["w"] == [0, -1]
    assert rows[2]["z"] == [0, Fraction(3, 4)] and rows[2]["w"] == [Fraction(-1, 4), 0]
    assert rows[3]["z"] == [Fraction(1, 6), Fraction(2, 3)] and rows[3]["w"] == [0, 0]
    figure = FIGURES["complementarity-active-sets.svg"]()
    for text in ("接触なし（w&lt;0）", "Aだけ（w&lt;0）", "Bだけ（w&lt;0）", "AとB（解）"):
        assert text in figure
    assert figure.count('fill="#b3532d"') == 1  # only the solution is drawn filled
