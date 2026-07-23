from pathlib import Path

from optimization_compass.content_models import load_content
from optimization_compass.content_quality import style_warnings


def test_lp_qp_conic_guide_connects_cross_domain_risk_lessons() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    guide = pages["lp-qp-conic"]

    assert "S103" in guide.source_ids
    assert guide.visualization_ids == (
        "portfolio-nominal-8-4",
        "portfolio-cvar-8-4",
    )
    assert guide.comparison_ids == (
        "COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4",
        "COMPARE_ENERGY_NOMINAL_CVAR_8_4",
    )
    for route in (
        "#/gallery/portfolio-cvar-allocation",
        "#/gallery/energy-cvar-procurement",
        "#/theater/learning/SCENARIO_PORTFOLIO_NOMINAL_8_4",
        "#/theater/learning/SCENARIO_PORTFOLIO_CVAR_8_4",
        "#/compare/COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4",
        "#/compare/COMPARE_ENERGY_NOMINAL_CVAR_8_4",
    ):
        assert route in guide.body

    assert "電力市場／需要／送電網／契約を再現しません" in guide.body
    assert "一般性能rankingや確率保証" in guide.body


def test_active_set_qp_separates_working_set_and_operator_splitting() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    guide = pages["active-set-qp"]

    for route in (
        "#/learn/active-set",
        "#/learn/admm-qp",
        "#/learn/barrier-lp-qp",
        "#/learn/lp-qp-conic",
    ):
        assert route in guide.body

    assert "OSQPのようなoperator-splitting型" in guide.body
    assert "working setとは別の反復を使います" in guide.body
    assert style_warnings(guide) == ()


def test_primal_dual_conic_keeps_residuals_and_solver_layers_visible() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    guide = pages["primal-dual-conic"]

    for route in (
        "#/learn/barrier-lp-qp",
        "#/learn/lp-qp-conic",
        "#/learn/interior-point-nlp",
    ):
        assert route in guide.body

    for diagnostic in (
        "primal feasibility residual",
        "dual feasibility residual",
        "duality gap",
    ):
        assert diagnostic in guide.body

    assert style_warnings(guide) == ()
