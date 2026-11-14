from __future__ import annotations

from scripts.lesson_figures.assignment_matching import FIGURES


def test_assignment_figures_use_the_article_numbers() -> None:
    from scripts.lesson_figures.assignment_matching import (
        ASSIGN_TIMES,
        ASSIGN_U,
        ASSIGN_V,
        assignment_all,
        assignment_greedy,
        assignment_reduced,
    )

    rows = assignment_all()
    assert [(total, longest) for total, longest, _ in rows] == [
        (15, 9),
        (16, 8),
        (20, 10),
        (21, 10),
        (22, 14),
        (24, 14),
    ]
    assert rows[0][2] == (0, 1, 2)
    assert assignment_greedy() == [(0, 1), (1, 2), (2, 0)]
    # The row and column values certify the minimum: never above a time, and summing to 15.
    reduced = assignment_reduced()
    assert all(value >= 0 for row in reduced for value in row)
    assert [reduced[i][i] for i in range(3)] == [0, 0, 0]
    assert sum(ASSIGN_U) + sum(ASSIGN_V) == 15
    assert sum(reduced[i][j] for i, j in assignment_greedy()) == 24 - 15
    assert ASSIGN_TIMES[2][2] == 9
    greedy = FIGURES["assignment-greedy-optimal.svg"]()
    for text in ("合計 24 分", "合計 15 分", "2 + 8 + 14 = 24", "3 + 3 + 9 = 15"):
        assert text in greedy
    dual = FIGURES["assignment-dual-bound.svg"]()
    for text in ("u の合計 9 ＋ v の合計 6 = 15", "救急車3 u=5", "C v=4"):
        assert text in dual
