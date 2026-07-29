from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

import pytest

from scripts.generate_article_figures import (
    _active_set_qp_probe,
    _cp_search_probe,
    _dijkstra_astar_grid_probe,
    _direct_shooting_probe,
    _dynamic_programming_knapsack_probe,
    _epsilon_constraint_production_probe,
    _finite_horizon_lqr_probe,
    _local_search_two_opt_probe,
    _multiple_shooting_probe,
    _network_simplex_transport_probe,
    _particle_swarm_probe,
    _pbt_population_probe,
    _pdlp_probe,
    _sgd_mini_batch_probe,
    _simulated_annealing_probe,
    _spatial_branch_bound_probe,
    _spatial_interval_lower_bound,
    _spatial_objective,
    generate_article_figures,
    read_dataset_version,
)

ROOT = Path(__file__).parents[1]
VERSION = read_dataset_version()


def test_active_set_qp_probe_adds_and_removes_constraints_sequentially() -> None:
    probe = _active_set_qp_probe()
    events = probe["events"]

    assert [(event["action"], event["constraint_index"]) for event in events] == [
        ("remove", 0),
        ("add", 2),
        ("remove", 1),
        ("add", 3),
        ("optimal", None),
    ]
    assert [event["working_set"] for event in events] == [
        (1,),
        (1, 2),
        (2,),
        (2, 3),
        (2, 3),
    ]
    assert probe["initial_point"] == pytest.approx((0.0, 0.0))
    assert probe["final_point"] == pytest.approx((1.5, 0.5))
    assert probe["initial_objective"] == pytest.approx(0.0)
    assert probe["final_objective"] == pytest.approx(-4.125)
    assert probe["max_residual"] == pytest.approx(0.0)


def test_direct_shooting_probe_keeps_controls_and_rollout_states_separate() -> None:
    probe = _direct_shooting_probe()

    assert len(probe["initial_controls"]) == len(probe["optimized_controls"]) == 20
    assert len(probe["initial_states"]) == len(probe["optimized_states"]) == 21
    assert len(probe["history"]) == 81
    assert probe["initial_objective"] == pytest.approx(1.0)
    assert probe["optimized_controls"][0] == pytest.approx(0.5075261591704722)
    assert probe["optimized_controls"][8] == pytest.approx(0.9889078241953825)
    assert probe["optimized_controls"][9:] == pytest.approx((1.0,) * 11)
    assert probe["optimized_states"][-1] == pytest.approx(0.9503875701362733)
    assert probe["final_objective"] == pytest.approx(0.03435619268834956)
    assert probe["terminal_error"] == pytest.approx(0.049612429863726715)
    assert probe["saturated_controls"] == 11


def test_dijkstra_and_astar_find_equal_cost_with_different_expansion_areas() -> None:
    probe = _dijkstra_astar_grid_probe()
    dijkstra = probe["dijkstra"]
    astar = probe["astar"]

    assert dijkstra["cost"] == astar["cost"] == 24
    assert len(dijkstra["path"]) == len(astar["path"]) == 25
    assert len(dijkstra["expanded"]) == 168
    assert len(astar["expanded"]) == 92
    assert dijkstra["relaxed_edges"] == 169
    assert astar["relaxed_edges"] == 125
    assert probe["expansion_reduction"] == pytest.approx(76 / 168)


def test_cp_search_probe_prunes_failed_queen_branches_before_backtracking() -> None:
    probe = _cp_search_probe()
    events = probe["events"]

    assert probe["solution"] == ((0, 1), (1, 3), (2, 0), (3, 2))
    assert probe["nodes"] == 8
    assert probe["pruned_values"] == 29
    assert probe["conflicts"] == 2
    assert probe["backtracks"] == 2
    assert [event["action"] for event in events] == [
        "assign",
        "assign",
        "conflict",
        "assign",
        "assign",
        "conflict",
        "backtrack",
        "backtrack",
        "assign",
        "assign",
        "assign",
        "assign",
        "solution",
    ]
    assert events[0]["domains"] == ((0,), (2, 3), (1, 3), (1, 2))
    assert events[4]["domains"] == ((0,), (3,), (1,), ())
    assert events[-1]["domains"] == ((1,), (3,), (0,), (2,))


def test_dynamic_programming_probe_fills_table_and_backtracks_selected_items() -> None:
    probe = _dynamic_programming_knapsack_probe()

    assert probe["table"] == (
        (0, 0, 0, 0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 8, 8, 8, 8, 8),
        (0, 0, 0, 5, 8, 8, 8, 13, 13),
        (0, 0, 0, 5, 8, 8, 8, 13, 13),
        (0, 0, 4, 5, 8, 9, 12, 13, 13),
    )
    assert probe["selected"] == (0, 1)
    assert probe["backtrack"] == ((4, 8), (3, 8), (2, 8), (1, 5), (0, 1))
    assert probe["selected_weight"] == 7
    assert probe["unused_capacity"] == 1
    assert probe["optimal_value"] == 13


def test_epsilon_constraint_probe_moves_along_pareto_plans_and_detects_infeasibility() -> None:
    probe = _epsilon_constraint_production_probe()

    assert probe["feasible_count"] == 88
    assert probe["pareto"] == (
        (6, 0, 18, 48, 36),
        (4, 3, 18, 53, 30),
        (2, 6, 18, 58, 24),
        (0, 9, 18, 63, 18),
    )
    assert probe["solutions"] == (
        (36, (6, 0, 18, 48, 36)),
        (30, (4, 3, 18, 53, 30)),
        (24, (2, 6, 18, 58, 24)),
        (18, (0, 9, 18, 63, 18)),
        (12, None),
    )
    assert probe["pareto_count"] == 4
    assert probe["solved_count"] == 4


def test_pdlp_probe_requires_all_three_stopping_quantities() -> None:
    probe = _pdlp_probe()
    history = probe["history"]

    assert len(history) == 101
    assert history[0]["primal"] == pytest.approx((1.0 / 3.0,) * 3)
    assert history[0]["dual_residual"] == pytest.approx(0.0)
    assert history[0]["primal_residual"] == pytest.approx(0.0)
    assert history[0]["objective_difference"] == pytest.approx(2.0)
    assert history[5]["dual_residual"] > 0.48
    assert probe["final_primal"] == pytest.approx((0.0, 1.0, 0.0), abs=3e-7)
    assert probe["final_dual"] == pytest.approx(1.0, abs=3e-7)
    assert probe["final_primal_residual"] < 3e-7
    assert probe["final_dual_residual"] < 3e-7
    assert probe["final_objective_difference"] < 4e-7


def test_network_simplex_probe_pivots_one_feasible_transport_tree() -> None:
    probe = _network_simplex_transport_probe()

    assert probe["entering"] == ("A", "Z")
    assert probe["leaving"] == ("A", "Y")
    assert probe["theta"] == pytest.approx(1.0)
    assert probe["initial_cost"] == pytest.approx(20.0)
    assert probe["optimized_cost"] == pytest.approx(18.0)
    assert probe["initial_reduced_costs"][("A", "Z")] == pytest.approx(-2.0)
    assert min(probe["optimized_reduced_costs"].values()) == pytest.approx(0.0)
    assert probe["optimized_flows"] == pytest.approx(
        {
            ("A", "X"): 3.0,
            ("A", "Y"): 0.0,
            ("A", "Z"): 1.0,
            ("B", "X"): 0.0,
            ("B", "Y"): 2.0,
            ("B", "Z"): 3.0,
        }
    )
    assert probe["initial_balance_error"] == pytest.approx(0.0)
    assert probe["optimized_balance_error"] == pytest.approx(0.0)


def test_local_search_probe_accepts_four_two_opt_reversals() -> None:
    probe = _local_search_two_opt_probe()
    history = probe["history"]

    assert probe["initial_tour"] == (0, 2, 4, 6, 1, 3, 5, 7)
    assert probe["final_tour"] == (0, 1, 2, 3, 4, 5, 6, 7)
    assert [item["move"] for item in history[1:]] == [
        (3, 6),
        (2, 5),
        (1, 2),
        (4, 5),
    ]
    assert probe["initial_length"] == pytest.approx(29.071445620639636)
    assert probe["final_length"] == pytest.approx(16.882399368664082)
    assert probe["relative_improvement"] == pytest.approx(0.41927898636460614)
    assert probe["accepted_moves"] == 4
    assert probe["evaluated_candidates"] == 105
    assert probe["initial_crossings"] == 5
    assert probe["final_crossings"] == 0


def test_lqr_probe_matches_the_fixed_article_equations() -> None:
    states, controls, gains = _finite_horizon_lqr_probe()

    assert len(states) == 41
    assert len(controls) == len(gains) == 40
    assert states[-1] == pytest.approx((2.7723676704340833e-05, 3.0156938335117316e-05))
    assert max(abs(value) for value in controls) == pytest.approx(15.208943465016517)
    assert gains[0] == pytest.approx((7.604471732508259, 4.977648136580166))


def test_multiple_shooting_probe_closes_the_fixed_continuity_defects() -> None:
    probe = _multiple_shooting_probe()
    initial = probe["initial"]
    solved = probe["solved"]

    assert isinstance(initial, dict)
    assert isinstance(solved, dict)
    assert initial["vector"] == pytest.approx((0.5, 0.5, 1.5))
    assert initial["defects"] == pytest.approx((-0.25, 0.25))
    assert initial["objective"] == pytest.approx(1.25)
    assert solved["vector"] == pytest.approx((0.5, 1.0, 1.0))
    assert solved["defects"] == pytest.approx((0.0, 0.0), abs=1e-12)
    assert solved["objective"] == pytest.approx(1.0)


def test_spatial_branch_bound_probe_closes_a_valid_interval_gap() -> None:
    probe = _spatial_branch_bound_probe()

    assert probe["best_point"] == pytest.approx(1.0)
    assert probe["best_value"] == pytest.approx(-1.0)
    assert probe["global_bound"] <= probe["best_value"]
    assert 0.0 <= probe["absolute_gap"] <= probe["gap_tolerance"]
    assert probe["explored"] == 70
    assert len(probe["pruned"]) == 25
    assert len(probe["pending"]) == 46


def test_spatial_interval_bound_stays_below_fixed_dense_probes() -> None:
    for lower, upper in ((0.0, 2.0), (0.5, 1.0), (0.75, 1.25), (1.0, 1.5)):
        bound = _spatial_interval_lower_bound(lower, upper)
        sampled_minimum = min(
            _spatial_objective(lower + index / 100 * (upper - lower)) for index in range(101)
        )
        assert bound <= sampled_minimum


def test_sgd_probe_keeps_batch_noise_separate_from_full_data_loss() -> None:
    probe = _sgd_mini_batch_probe()

    assert len(probe["path"]) == 65
    assert len(probe["history"]) == 64
    assert probe["initial_loss"] == pytest.approx(2.2409457290153965)
    assert probe["final_parameters"] == pytest.approx((1.803009481835502, -0.8936153197869711))
    assert probe["final_loss"] == pytest.approx(0.001566461485889374)
    assert probe["optimum_loss"] == pytest.approx(0.0015646508562708345)
    assert probe["upward_full_loss_steps"] == 5


def test_simulated_annealing_probe_accepts_worse_moves_while_preserving_best() -> None:
    probe = _simulated_annealing_probe()
    history = probe["history"]

    assert len(history) == 401
    assert probe["initial_objective"] == pytest.approx(32.25)
    assert probe["best_x"] == pytest.approx(-0.0019633254984749056)
    assert probe["best_objective"] == pytest.approx(0.000764721820644354)
    assert probe["accepted_moves"] == 65
    assert probe["accepted_worsening"] == 32
    assert probe["early_worsening"] == 18
    assert probe["late_worsening"] == 1
    assert all(
        float(current["best_objective"]) <= float(previous["best_objective"])
        for previous, current in zip(history, history[1:], strict=False)
    )


def test_pbt_probe_records_worker_copy_and_lineage_inheritance() -> None:
    probe = _pbt_population_probe()
    snapshots = probe["snapshots"]
    events = probe["events"]

    assert len(snapshots) == 11
    assert len(events) == 5
    assert [(event[0], event[1], event[2]) for event in events] == [
        (2, 5, 0),
        (4, 5, 1),
        (6, 4, 2),
        (8, 3, 0),
        (10, 0, 5),
    ]
    assert snapshots[0][0][3] == 0
    assert snapshots[2][0][3] == 5
    assert snapshots[8][0][3] == 3
    assert probe["initial_best"] == pytest.approx(-1.0032)
    assert probe["final_best"] == pytest.approx(-0.011770171589838159)
    assert probe["final_roots"] == (3, 4, 5)


def test_particle_swarm_probe_tracks_best_and_population_collapse() -> None:
    probe = _particle_swarm_probe()
    snapshots = probe["snapshots"]
    history = probe["history"]

    assert len(history) == 41
    assert [snapshot["iteration"] for snapshot in snapshots] == [0, 5, 15, 40]
    assert probe["initial_best_value"] == pytest.approx(6.090066675041227)
    assert probe["final_best"] == pytest.approx((-0.0005254906782732574, 1.868959781557364e-05))
    assert probe["final_best_value"] == pytest.approx(5.4853330098580955e-05)
    assert probe["initial_diversity"] == pytest.approx(4.625011539787717)
    assert probe["final_diversity"] == pytest.approx(0.212919919950744)
    assert probe["personal_updates"] == 219
    assert probe["boundary_hits"] == 0
    assert all(
        current["global_best_value"] <= previous["global_best_value"]
        for previous, current in zip(history, history[1:], strict=False)
    )


def test_article_figures_are_deterministic_and_current() -> None:
    assert "\n" not in VERSION
    first = generate_article_figures(VERSION)
    second = generate_article_figures(VERSION)

    assert first == second
    assert set(first) == {
        "active-set-qp-execution.svg",
        "bayesian-optimization-execution.svg",
        "constrained-feasibility-execution.svg",
        "cp-search-propagation-execution.svg",
        "direct-shooting-rollout-execution.svg",
        "dijkstra-astar-grid-execution.svg",
        "dynamic-programming-knapsack-execution.svg",
        "epsilon-constraint-production-execution.svg",
        "gradient-family-execution.svg",
        "lqr-backward-forward-execution.svg",
        "least-squares-fit-diagnostic.svg",
        "local-search-two-opt-execution.svg",
        "multiple-shooting-continuity-execution.svg",
        "network-simplex-pivot-execution.svg",
        "nelder-mead-execution.svg",
        "optimal-control-mesh-execution.svg",
        "pareto-preference-execution.svg",
        "particle-swarm-execution.svg",
        "pbt-lineage-execution.svg",
        "pdlp-residual-execution.svg",
        "portfolio-risk-execution.svg",
        "search-tree-proof-execution.svg",
        "sgd-mini-batch-execution.svg",
        "simulated-annealing-execution.svg",
        "so3-update-diagnostic.svg",
        "spatial-branch-bound-execution.svg",
        "topology-field-execution.svg",
        "trf-probe-execution.svg",
    }
    for name, payload in first.items():
        assert payload == (ROOT / "site" / "public" / "media" / name).read_bytes()


def test_article_figures_have_accessible_svg_titles_and_execution_provenance() -> None:
    figures = generate_article_figures(VERSION)

    for payload in figures.values():
        root = ElementTree.fromstring(payload)
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        assert root.attrib["role"] == "img"
        assert root.attrib["aria-labelledby"] == "figure-title figure-description"
        assert root.find("svg:title", namespace).text
        assert root.find("svg:desc", namespace).text
        assert "実行生成:" in payload.decode("utf-8")


def test_articles_place_execution_results_before_long_diagnostic_sections() -> None:
    expected = {
        "content/methods/active-set-qp.md": "active-set-qp-execution.svg",
        "content/methods/bayesian-optimization.md": "bayesian-optimization-execution.svg",
        "content/methods/family-expensive-black-box.md": "bayesian-optimization-execution.svg",
        "content/methods/gradient-descent.md": "gradient-family-execution.svg",
        "content/methods/adam.md": "gradient-family-execution.svg",
        "content/methods/momentum-sgd.md": "gradient-family-execution.svg",
        "content/methods/ilqr-ddp.md": "lqr-backward-forward-execution.svg",
        "content/methods/least-squares.md": "least-squares-fit-diagnostic.svg",
        "content/methods/local-search-combinatorial.md": "local-search-two-opt-execution.svg",
        "content/methods/multiple-shooting.md": "multiple-shooting-continuity-execution.svg",
        "content/methods/network-simplex.md": "network-simplex-pivot-execution.svg",
        "content/methods/projected-gradient.md": "so3-update-diagnostic.svg",
        "content/methods/riemannian-gradient.md": "so3-update-diagnostic.svg",
        "content/methods/family-manifold.md": "so3-update-diagnostic.svg",
        "content/methods/nelder-mead.md": "nelder-mead-execution.svg",
        "content/methods/branch-and-cut.md": "search-tree-proof-execution.svg",
        "content/methods/family-discrete-structure.md": "search-tree-proof-execution.svg",
        "content/methods/pbt.md": "pbt-lineage-execution.svg",
        "content/methods/pdlp.md": "pdlp-residual-execution.svg",
        "content/methods/particle-swarm.md": "particle-swarm-execution.svg",
        "content/methods/sgd.md": "sgd-mini-batch-execution.svg",
        "content/methods/simulated-annealing.md": "simulated-annealing-execution.svg",
        "content/methods/spatial-branch-and-bound.md": "spatial-branch-bound-execution.svg",
        "content/methods/simp-topology.md": "topology-field-execution.svg",
        "content/methods/density-filter.md": "topology-field-execution.svg",
        "content/methods/optimality-criteria-topology.md": "topology-field-execution.svg",
        "content/concepts/topology-optimization.md": "topology-field-execution.svg",
        "content/concepts/chance-risk-contract.md": "portfolio-risk-execution.svg",
        "content/methods/trust-region-reflective.md": "trf-probe-execution.svg",
        "content/methods/constrained-continuous.md": "constrained-feasibility-execution.svg",
        "content/methods/cp-search.md": "cp-search-propagation-execution.svg",
        "content/methods/direct-shooting.md": "direct-shooting-rollout-execution.svg",
        "content/methods/dijkstra-astar.md": "dijkstra-astar-grid-execution.svg",
        "content/methods/dynamic-programming.md": "dynamic-programming-knapsack-execution.svg",
        "content/methods/epsilon-constraint.md": "epsilon-constraint-production-execution.svg",
        "content/methods/dual-annealing.md": "simulated-annealing-execution.svg",
        "content/methods/family-constrained-nlp.md": "constrained-feasibility-execution.svg",
        "content/methods/slsqp.md": "constrained-feasibility-execution.svg",
        "content/methods/bfgs.md": "constrained-feasibility-execution.svg",
        "content/methods/weighted-sum.md": "pareto-preference-execution.svg",
        "content/methods/direct-collocation.md": "optimal-control-mesh-execution.svg",
        "content/methods/family-optimal-control.md": "optimal-control-mesh-execution.svg",
    }

    for relative_path, figure in expected.items():
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert figure in source
        closing_marker = source.find("## 次に読む")
        assert source.index(figure) < (closing_marker if closing_marker >= 0 else len(source))
