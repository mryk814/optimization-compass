from pathlib import Path

from optimization_compass.content_models import load_content

ROOT = Path(__file__).resolve().parents[1]


def _pages():
    return {page.content_id: page for page in load_content(ROOT / "content")}


def test_concepts_reference_their_canonical_learning_assets() -> None:
    pages = _pages()

    nested = pages["concept.nested-equilibrium-complementarity-hybrid"]
    assert "S064" in nested.source_ids
    assert "#/visualization/" not in nested.body
    assert "#/gallery/bilevel-regularized-regression" in nested.body
    assert "#/theater/learning/SCENARIO_BILEVEL_REGRESSION_EXACT" in nested.body
    assert "#/theater/learning/SCENARIO_BILEVEL_REGRESSION_RELAXED" in nested.body
    assert "#/theater/learning/SCENARIO_HYBRID_MODE_CHATTERING" in nested.body

    pde = pages["concept.pde-constrained-optimization"]
    assert pde.visualization_ids == (
        "pde-state-tolerance-tight",
        "pde-state-tolerance-loose",
        "pde-state-solve-failure",
    )
    assert pde.comparison_ids == ("COMPARE_PDE_STATE_TOLERANCE_COST",)

    uncertainty = pages["concept.uncertainty-models"]
    assert "S103" in uncertainty.source_ids
    assert uncertainty.visualization_ids == (
        "portfolio-nominal-8-4",
        "portfolio-cvar-8-4",
    )
    assert uncertainty.comparison_ids == ("COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4",)
    assert "#/theater/learning/SCENARIO_PORTFOLIO_CVAR_8_4" in uncertainty.body
    assert "#/compare/COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4" in uncertainty.body

    so3 = pages["concept.so3-rotation-representation"]
    assert "S107" in so3.source_ids
    assert so3.visualization_ids == (
        "so3-projected-alignment",
        "so3-riemannian-alignment",
    )
    assert so3.comparison_ids == ("COMPARE_SO3_PROJECTED_RIEMANNIAN",)
    assert "#/gallery/so3-attitude-alignment" in so3.body
    assert "#/theater/learning/SCENARIO_SO3_PROJECTED_ALIGNMENT" in so3.body
    assert "#/theater/learning/SCENARIO_SO3_RIEMANNIAN_ALIGNMENT" in so3.body
    assert "#/compare/COMPARE_SO3_PROJECTED_RIEMANNIAN" in so3.body


def test_concepts_scope_failed_evaluations_and_quotient_ambiguity() -> None:
    pages = _pages()

    pde = pages["concept.pde-constrained-optimization"]
    assert "この教材のreduced formulationでは" in pde.body
    assert "state solveが停止した評価をvalidな観測として扱いません" in pde.body
    assert "stateに依存する目的値を確定できないためです" in pde.body

    spd = pages["concept.spd-matrix-geometry"]
    assert "$Q$を直交行列とすると" in spd.body
