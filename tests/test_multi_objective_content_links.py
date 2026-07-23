from pathlib import Path

from optimization_compass.content_models import load_content


def test_multi_objective_guide_separates_front_generation_from_preference() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    multi_objective = pages["multi-objective"]

    assert multi_objective.visualization_ids == ("biobjective-quadratic-pareto-front",)
    assert multi_objective.comparison_ids == ("COMPARE_PARETO_PREFERENCE",)
    assert "#/theater/multi-objective" in multi_objective.body
    assert "#/compare/COMPARE_PARETO_PREFERENCE" in multi_objective.body
    assert "手法性能のbenchmarkではなく" in multi_objective.body
    assert "一般の非凸front" in multi_objective.body
