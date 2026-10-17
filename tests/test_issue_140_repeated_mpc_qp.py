from __future__ import annotations

import json
from pathlib import Path

from optimization_compass.comparisons import load_comparison_seed
from optimization_compass.dataset_release import build_staged_release
from optimization_compass.repeated_mpc_qp import (
    COLD_SCENARIO_ID,
    COLD_TRACE_ID,
    PROBLEM_INSTANCE_ID,
    WARM_SCENARIO_ID,
    WARM_TRACE_ID,
    build_repeated_mpc_qp_scenario,
    generate_repeated_mpc_qp_traces,
)


def test_repeated_mpc_qp_ledger_separates_residuals_from_deadline_margin() -> None:
    warm, cold = generate_repeated_mpc_qp_traces(dataset_version="test")

    assert warm.trace_id == WARM_TRACE_ID
    assert cold.trace_id == COLD_TRACE_ID
    assert warm.objective_id == cold.objective_id == PROBLEM_INSTANCE_ID
    assert [frame.oracle_evaluations for frame in warm.frames] == [1, 2, 3, 4]
    assert warm.frames[0].payload["warm_start"] is False
    assert warm.frames[1].payload["warm_start"] is True
    assert cold.frames[1].payload["warm_start"] is False
    assert warm.frames[1].payload["deadline_status"] == "met"
    assert cold.frames[1].payload["deadline_status"] == "met"
    assert cold.frames[0].payload["deadline_status"] == "missed"
    assert warm.frames[1].metrics[4].value < cold.frames[1].metrics[4].value


def test_repeated_mpc_qp_scenarios_are_scope_limited_metric_history() -> None:
    warm, cold = generate_repeated_mpc_qp_traces(dataset_version="test")
    warm_scenario = build_repeated_mpc_qp_scenario(warm)
    cold_scenario = build_repeated_mpc_qp_scenario(cold)

    assert {warm_scenario.scenario_id, cold_scenario.scenario_id} == {
        WARM_SCENARIO_ID,
        COLD_SCENARIO_ID,
    }
    assert warm_scenario.purpose == "mechanism"
    assert cold_scenario.purpose == "sensitivity"
    assert cold_scenario.lesson.failure_signals
    assert warm_scenario.artifact.renderer_family == "generic_metric_history"
    assert "CPU time" in warm_scenario.lesson.limitations_en


def test_ec025_connects_its_own_instance_scenarios_and_comparison() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "EC025")
    comparisons = load_comparison_seed(Path("data/seeds/site_comparisons.json"), "test")
    comparison = next(
        item
        for item in comparisons.comparisons
        if item.comparison_id == "COMPARE_REPEATED_MPC_QP_WARM_START"
    )

    assert {WARM_SCENARIO_ID, COLD_SCENARIO_ID} <= set(case["visualization_ids"])
    assert case["comparison_ids"] == ["COMPARE_REPEATED_MPC_QP_WARM_START"]
    assert comparison.problem_instance_id == PROBLEM_INSTANCE_ID
    assert comparison.benchmark_context_id == "BENCH_REPEATED_MPC_QP_EC025_4"
    assert comparison.changed_factors == ["第2周期以降に前周期解をwarm startとして渡すかどうかだけ"]
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False


def test_staged_ec025_journey_is_complete(tmp_path: Path) -> None:
    release = build_staged_release(
        Path("data/optimization_method_selection_database_v0.2.0.sqlite"), tmp_path / "release"
    )
    journeys = json.loads(
        (release.site_data_directory / "learning-journeys.json").read_text(encoding="utf-8")
    )
    journey = next(item for item in journeys["journeys"] if item["journey_id"] == "EC025")

    assert journey["status"] == "complete"
    assert journey["completion_reasons"] == []
