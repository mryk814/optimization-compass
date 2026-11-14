from __future__ import annotations

from scripts.lesson_figures.mixed_integer_linear_program import (
    FIGURES,
    MILP_NODES,
    milp_integer_points,
    milp_relaxation,
)


def test_milp_tree_figure_uses_the_article_numbers() -> None:
    from fractions import Fraction

    points = milp_integer_points()
    assert len(points) == 13
    assert max(points, key=lambda p: 5 * p[0] + 4 * p[1]) == (4, 0)
    solved = {name: milp_relaxation(extra) for name, _, extra in MILP_NODES}
    expected = {
        "root": ((Fraction(3), Fraction(3, 2)), Fraction(21)),
        "left": ((Fraction(10, 3), Fraction(1)), Fraction(62, 3)),
        "left_left": ((Fraction(3), Fraction(1)), Fraction(19)),
        "left_right": ((Fraction(4), Fraction(0)), Fraction(20)),
        "right": ((Fraction(2), Fraction(2)), Fraction(18)),
    }
    assert solved == expected
    # Both leaves that give a final answer are integer points, and 19, 20, 18 never exceed 20.
    assert max(solved[n][1] for n in ("left_left", "left_right", "right")) == 20
    figure = FIGURES["milp-relaxation-tree.svg"]()
    for text in ("(10/3, 1)", "上界 62/3", "(3, 1.5)", "値 19", "値 20", "上界 18"):
        assert text in figure
    assert "stroke-dasharray" not in figure
