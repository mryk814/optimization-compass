from pathlib import Path

from optimization_compass.content_models import load_content
from optimization_compass.content_quality import style_warnings

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
    assert style_warnings(nested) == ()

    pde = pages["concept.pde-constrained-optimization"]
    assert pde.visualization_ids == (
        "pde-state-tolerance-tight",
        "pde-state-tolerance-loose",
        "pde-state-solve-failure",
    )
    assert pde.comparison_ids == ("COMPARE_PDE_STATE_TOLERANCE_COST",)
    assert style_warnings(pde) == ()

    evaluation_cost = pages["concept.evaluation-cost"]
    assert "#/compare/COMPARE_BO_MULTIFIDELITY_COST" in evaluation_cost.body
    assert (
        "#/theater/bayesian-optimization/SCENARIO_BO_1D_LOW_FIDELITY_BIAS" in evaluation_cost.body
    )
    assert style_warnings(evaluation_cost) == ()

    uncertainty = pages["concept.uncertainty-models"]
    assert "S103" in uncertainty.source_ids
    assert uncertainty.visualization_ids == (
        "portfolio-nominal-8-4",
        "portfolio-cvar-8-4",
    )
    assert uncertainty.comparison_ids == ("COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4",)
    assert "#/theater/learning/SCENARIO_PORTFOLIO_CVAR_8_4" in uncertainty.body
    assert "#/compare/COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4" in uncertainty.body
    assert style_warnings(uncertainty) == ()

    chance_risk = pages["concept.chance-risk-contract"]
    assert chance_risk.visualization_ids == (
        "portfolio-nominal-8-4",
        "portfolio-cvar-8-4",
    )
    assert chance_risk.comparison_ids == ("COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4",)
    for route in (
        "#/theater/learning/SCENARIO_PORTFOLIO_NOMINAL_8_4",
        "#/theater/learning/SCENARIO_PORTFOLIO_CVAR_8_4",
        "#/compare/COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4",
    ):
        assert route in chance_risk.body
    assert "risk treatmentだけをcontrast-onlyで読みます" in chance_risk.body
    assert "一般性能rankingや将来分布への保証ではありません" in chance_risk.body
    assert style_warnings(chance_risk) == ()

    constraint_class = pages["concept.constraint-class"]
    for route in (
        "#/learn/projected-gradient",
        "#/learn/family.constrained-nlp",
        "#/learn/family.discrete-structure",
    ):
        assert route in constraint_class.body
    for constraint_oracle in (
        "`g(x)`の値",
        "Jacobian",
        "Boolean論理",
        "simulationが失敗した後",
    ):
        assert constraint_oracle in constraint_class.body
    assert "式／単位／tolerance／判定時点" in constraint_class.body
    assert style_warnings(constraint_class) == ()

    variable_domain = pages["concept.variable-domain"]
    for route in (
        "#/learn/family.smooth-local",
        "#/learn/family.discrete-structure",
        "#/learn/family.manifold",
    ):
        assert route in variable_domain.body
    assert style_warnings(variable_domain) == ()

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
