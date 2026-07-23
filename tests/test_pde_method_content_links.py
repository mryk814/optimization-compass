from pathlib import Path

from optimization_compass.content_models import load_content


def test_adjoint_sensitivity_exposes_primary_pde_lessons_before_loose_run() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    adjoint = pages["adjoint-sensitivity"]

    assert adjoint.visualization_ids == (
        "topology-optimization-field-evolution",
        "pde-state-tolerance-tight",
        "pde-state-solve-failure",
    )
    assert adjoint.comparison_ids == ("COMPARE_PDE_STATE_TOLERANCE_COST",)
    for route in (
        "#/theater/learning/SCENARIO_TOPOLOGY_SIMP_OC",
        "#/theater/learning/SCENARIO_PDE_STATE_TOLERANCE_TIGHT",
        "#/compare/COMPARE_PDE_STATE_TOLERANCE_COST",
        "#/theater/learning/SCENARIO_PDE_STATE_SOLVE_FAILURE",
    ):
        assert route in adjoint.body

    assert "loose toleranceの個別runは比較が引き受け" in adjoint.body
    assert "実runtimeやmesh independenceを示しません" in adjoint.body
