from pathlib import Path

from optimization_compass.content_models import load_content


def test_existing_method_guides_expose_their_canonical_learning_assets() -> None:
    pages = {page.content_id: page for page in load_content(Path("content"))}
    expected = {
        "admm-qp": (
            ("repeated-mpc-qp-warm-start", "repeated-mpc-qp-cold-start"),
            ("COMPARE_REPEATED_MPC_QP_WARM_START",),
            "#/compare/COMPARE_REPEATED_MPC_QP_WARM_START",
            "実機遅延を必ず改善するとも主張しません",
        ),
        "branch-and-cut": (
            ("binary-knapsack-bnb-complete", "binary-knapsack-bnb-budget"),
            ("COMPARE_KNAPSACK_BNB_BUDGET",),
            "#/compare/COMPARE_KNAPSACK_BNB_BUDGET",
            "カットの生成、カット生成の繰り返し、根の緩和の強化そのものは表示しません",
        ),
        "family.constrained-nlp": (
            ("constrained-disk-feasible-region",),
            (),
            "#/theater/learning/SCENARIO_CONSTRAINED_DISK",
            "実装性能を順位付けする図ではありません",
        ),
        "gauss-newton": (
            ("root-finding-component-tolerance", "root-finding-small-squared-residual"),
            ("COMPARE_ROOT_FINDING_COMPONENT_TOLERANCE",),
            "#/compare/COMPARE_ROOT_FINDING_COMPONENT_TOLERANCE",
            "収束速度も順位付けしません",
        ),
        "local-search-combinatorial": (
            ("time-window-routing-feasible", "time-window-routing-violation"),
            ("COMPARE_TIME_WINDOW_ROUTING_HARD_CONSTRAINT",),
            "#/compare/COMPARE_TIME_WINDOW_ROUTING_HARD_CONSTRAINT",
            "経路品質の性能比較ではありません",
        ),
        "mads": (
            ("failed-simulation-feasible-ledger", "failed-simulation-failure-ledger"),
            ("COMPARE_FAILED_SIMULATION_STATUS_LEDGER",),
            "#/compare/COMPARE_FAILED_SIMULATION_STATUS_LEDGER",
            "実設計品質のベンチマークではありません",
        ),
    }

    for content_id, (visualizations, comparisons, route, caveat) in expected.items():
        page = pages[content_id]
        assert page.visualization_ids == visualizations
        assert page.comparison_ids == comparisons
        assert route in page.body
        assert caveat in page.body
