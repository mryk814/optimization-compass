from __future__ import annotations

from scripts.lesson_figures.vehicle_routing import FIGURES, vrp_data


def test_vrp_figures_use_the_article_numbers() -> None:
    data = vrp_data()
    assert data["split_count"] == 22
    assert round(data["optimum"], 3) == 35.527  # type: ignore[arg-type]
    assert data["optimum_routes"] == [[3, 1, 4, 6], [2, 7, 5]]
    assert round(data["nearest"], 3) == 39.616  # type: ignore[arg-type]
    assert data["nearest_routes"] == [[4, 6, 7, 5], [3, 1, 2]]
    assert round(data["heuristic"], 3) == 38.508  # type: ignore[arg-type]
    assert data["heuristic_routes"] == [[4, 5, 7, 6], [1, 3, 2]]
    assert round(data["degree_cost"], 3) == 28.389  # type: ignore[arg-type]
    assert data["degree_routes"] == [[4], [6]]
    assert data["degree_loops"] == [[1, 3], [2, 5, 7]]
    figures = {name: draw() for name, draw in FIGURES.items()}
    assert "最近傍法と2-optの結果は38.508、全探索の最適は35.527" in figures["vrp-routes.svg"]
    assert "費用28.389の解が選ばれます" in figures["vrp-subtour.svg"]
    assert "輪が2つ残り" in figures["vrp-subtour.svg"]
    assert "stroke-dasharray" not in figures["vrp-routes.svg"] + figures["vrp-subtour.svg"]
