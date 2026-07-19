from __future__ import annotations

import json
from pathlib import Path

from optimization_compass.comparisons import load_comparison_seed
from optimization_compass.problem_registry import load_problem_suite
from optimization_compass.site_export import (
    _generate_optimal_control_history_trace,
    _generate_optimal_control_traces,
    _visualization_scenario,
)
from optimization_compass.visualization_scenarios import scenario_identity

ROOT = Path(__file__).parents[1]


def test_ec029_declares_the_pendulum_direct_collocation_flagship() -> None:
    payload = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in payload["cases"] if item["case_id"] == "EC029")

    assert [item["method_id"] for item in case["candidate_methods"]] == ["M_DIRECT_COLLOCATION"]
    assert "dynamics defect" in case["candidate_methods"][0]["reason"]
    assert "mesh（knot）数 $N=20$" in case["variable_domain"]
    assert "decision object" in case["decision_variables"]
    assert "defect" in case["constraints"]
    assert "x_0=(0,0)" in case["constraints"]
    assert "x_N=(\\pi,0)" in case["constraints"]
    assert "path／bound制約" in case["constraints"]
    assert "max dynamics defect" in case["practical_notes"]
    assert "node path tolerance $10^{-4}$" in case["practical_notes"]
    assert "再構成" in case["practical_notes"]
    assert "連続時間の可行性" in case["limitations"][0]
    assert "pendulum" in case["question"]
    assert case["comparison_ids"] == ["COMPARE_PENDULUM_COLLOCATION_MESH"]
    assert {
        "SCENARIO_PENDULUM_SWING_UP_MESH_20",
        "SCENARIO_PENDULUM_SWING_UP_MESH_40",
        "SCENARIO_PENDULUM_SWING_UP_MODEL_MISMATCH",
    } <= set(case["visualization_ids"])
    assert "#/gallery/EC025" in case["practical_notes"]
    assert "nested-equilibrium-complementarity-hybrid" in case["practical_notes"]


def test_pendulum_flagship_is_a_new_instance_without_repurposing_ec020() -> None:
    instances = {item.problem_instance_id: item for item in load_problem_suite().instances}

    assert "INSTANCE_OPTIMAL_CONTROL_EC020" in instances
    pendulum = instances["INSTANCE_PENDULUM_SWING_UP_EC020"]
    assert pendulum.registry_key == "problem.optimal_control.pendulum_swing_up.v1"
    assert pendulum.parameters["mesh_nodes"] == 20
    assert pendulum.parameters["terminal_target"] == [3.141592653589793, 0.0]
    assert {item["constraint_id"] for item in pendulum.constraints} == {
        "dynamics_defect",
        "initial_state",
        "terminal_target",
        "path_bounds",
    }
    assert "node／collocation point" in pendulum.limitations_ja


def test_existing_ec020_case_instance_scenario_and_trace_identity_are_unchanged() -> None:
    payload = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in payload["cases"] if item["case_id"] == "EC020")
    instances = {item.problem_instance_id: item for item in load_problem_suite().instances}
    trace = _generate_optimal_control_history_trace(dataset_version="0.18.9")

    assert case["title_ja"] == "非線形動力学を含む軌道を最適化する"
    assert case["title_en"] == "Optimize a trajectory with nonlinear dynamics"
    assert case["objective"] == (
        "参照軌道との差である追従誤差（tracking error）、制御入力の大きさ（control effort）、"
        "所要時間を重み付けし、$f=\\sum\\lVert x_k-x_{ref,k}\\rVert_Q^2+"
        "\\sum\\lVert u_k\\rVert_R^2+\\rho T$ を最小化する。"
    )
    assert case["visualization_ids"] == [
        "VIEW_PROBLEM_STRUCTURE",
        "SCENARIO_OPTIMAL_CONTROL_EC020",
    ]
    assert instances["INSTANCE_OPTIMAL_CONTROL_EC020"].registry_key == (
        "problem.optimal_control.ec020.v1"
    )
    assert trace.trace_id == "optimal-control-ec020-history"
    assert trace.objective_id == "INSTANCE_OPTIMAL_CONTROL_EC020"
    assert trace.scenario_id == "SCENARIO_OPTIMAL_CONTROL_EC020"
    assert trace.objective == {
        "kind": "trajectory_tracking_plus_control_effort",
        "mesh_nodes": 20,
    }


def test_optimal_control_theater_has_primary_sensitivity_and_independent_failure() -> None:
    traces = _generate_optimal_control_traces(dataset_version="0.18.9")
    scenarios = {trace.scenario_id: _visualization_scenario(trace) for trace in traces}

    assert set(scenarios) == {
        "SCENARIO_PENDULUM_SWING_UP_MESH_20",
        "SCENARIO_PENDULUM_SWING_UP_MESH_40",
        "SCENARIO_PENDULUM_SWING_UP_MODEL_MISMATCH",
    }
    assert scenarios["SCENARIO_PENDULUM_SWING_UP_MESH_20"].lesson.comparison_role == (
        "primary_example"
    )
    assert (
        scenarios["SCENARIO_PENDULUM_SWING_UP_MESH_40"].lesson.comparison_role
        == "sensitivity_variant"
    )
    failure = scenarios["SCENARIO_PENDULUM_SWING_UP_MODEL_MISMATCH"]
    assert failure.purpose == "failure_contrast"
    assert failure.lesson.comparison_role == "failure_contrast"
    assert "model" in failure.lesson.failure_signals[0].signal_id
    assert scenario_identity("SCENARIO_PENDULUM_SWING_UP_MESH_20") == (
        "canonical",
        "SCENARIO_PENDULUM_SWING_UP_MESH_20",
    )
    assert scenario_identity("SCENARIO_PENDULUM_SWING_UP_MESH_40") == (
        "derived",
        "SCENARIO_PENDULUM_SWING_UP_MESH_20",
    )
    final_payloads = {trace.scenario_id: trace.frames[-1].payload for trace in traces}
    assert final_payloads["SCENARIO_PENDULUM_SWING_UP_MESH_20"]["node_path_violation"] < 1e-4
    assert (
        final_payloads["SCENARIO_PENDULUM_SWING_UP_MESH_20"]["reconstructed_path_violation"] > 1e-4
    )
    assert final_payloads["SCENARIO_PENDULUM_SWING_UP_MODEL_MISMATCH"]["terminal_error"] > 0.1


def test_pendulum_mesh_compare_is_aligned_contrast_only() -> None:
    index = load_comparison_seed(
        ROOT / "data/seeds/site_comparisons.json", dataset_version="0.18.9"
    )
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_PENDULUM_COLLOCATION_MESH"
    )

    assert comparison.problem_instance_id == "INSTANCE_PENDULUM_SWING_UP_EC020"
    assert comparison.benchmark_context_id == "BENCH_PENDULUM_COLLOCATION_MESH_8"
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False
    assert comparison.budget.metric == comparison.synchronization_axis == "oracle_evaluations"
    fixed = " ".join(comparison.fixed_factors)
    for required in (
        "pendulum model",
        "horizon",
        "initial state",
        "terminal target",
        "path and bound constraints",
        "oracle evaluation budget",
        "dynamics defect tolerance",
        "node path tolerance",
        "terminal tolerance",
    ):
        assert required in fixed
    assert comparison.changed_factors == ["mesh nodes only: N=20 versus N=40"]
    assert {member.parameters["mesh_nodes"] for member in comparison.members} == {20, 40}
    assert {member.scenario_id for member in comparison.members} == {
        "SCENARIO_PENDULUM_SWING_UP_MESH_20",
        "SCENARIO_PENDULUM_SWING_UP_MESH_40",
    }
    assert all(member.budget == comparison.budget for member in comparison.members)


def test_pendulum_sources_are_primary_and_scope_is_explicit() -> None:
    migration = (ROOT / "data/migrations/014_optimal_control_pendulum.sql").read_text(
        encoding="utf-8"
    )
    assert "BENCH_PENDULUM_COLLOCATION_MESH_8" in migration
    assert "educational.optimal_control.v1" in migration
    assert 'comparison_scope":"exact' in migration
    assert "['S042','S050','S102']" not in migration
    assert '["S042","S050","S102"]' in migration
    assert "https://underactuated.mit.edu/trajopt.html" in migration


def test_ec020_generated_journey_keeps_the_existing_direct_collocation_reading_link() -> None:
    payload = json.loads(
        (ROOT / "site/public/data/learning-journeys.json").read_text(encoding="utf-8")
    )
    journey = next(item for item in payload["journeys"] if item["case_id"] == "EC020")

    assert "direct-collocation" in journey["content_ids"]
