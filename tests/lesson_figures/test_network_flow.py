from __future__ import annotations

from scripts.lesson_figures.network_flow import FIGURES


def test_network_flow_figure_uses_the_article_numbers() -> None:
    from scripts.lesson_figures.network_flow import flow_cost, flow_successive_paths

    pushes = flow_successive_paths()
    assert [(path, cost, sent) for path, cost, sent, _ in pushes] == [
        ("S→A→B→T", 3, 3),
        ("S→B→A→T", 8, 1),
    ]
    final = pushes[-1][3]
    assert final == {("S", "A"): 3, ("S", "B"): 1, ("A", "B"): 2, ("A", "T"): 1, ("B", "T"): 3}
    assert flow_cost(pushes[0][3]) == 9 and flow_cost(final) == 17
    # Without reverse arcs the greedy run stops after three boxes.
    stuck = flow_successive_paths(use_reverse=False)
    assert sum(sent for _, _, sent, _ in stuck) == 3
    figure = FIGURES["network-flow-paths.svg"]()
    for text in ("費用 9", "費用 17", "4−1+5=8", "3/3（満杯）"):
        assert text in figure
    assert "stroke-dasharray" not in figure
