from __future__ import annotations

from scripts.lesson_figures.shortest_path import FIGURES


def test_shortest_path_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.shortest_path import (
        path_distances,
        path_routes,
        path_rules,
        path_total,
    )

    totals = sorted((path_total(route), "→".join(route)) for route in path_routes())
    assert totals == [(7, "S→B→C→T"), (8, "S→A→T"), (10, "S→A→B→C→T"), (12, "S→T")]
    dist, best = path_distances()
    assert dist == {"S": 0, "A": 2, "B": 4, "C": 5, "T": 7}
    assert best == ("S", "B", "C", "T")
    assert [(name, path_total(route)) for name, route in path_rules()] == [
        ("道の数が最少", 12),
        ("次の道が最安", 10),
        ("合計が最小", 7),
    ]
    figure = FIGURES["shortest-path-routes.svg"]()
    for text in ("d=7", "S→A→B→C→T（道4本）", "S→B→C→T（道3本）", "12分", "10分", "7分"):
        assert text in figure
    assert "stroke-dasharray" not in figure
