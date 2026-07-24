from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.comparisons import load_comparison_seed
from optimization_compass.failed_simulation import (
    FAILURE_SCENARIO_ID,
    PROBLEM_INSTANCE_ID,
    build_failed_simulation_scenario,
    generate_failed_simulation_traces,
)
from optimization_compass.problem_registry import get_runtime_problem


def test_failed_simulation_keeps_status_outside_the_objective() -> None:
    feasible, failure = generate_failed_simulation_traces(dataset_version="test")
    failed_frame = failure.frames[4]

    assert failure.terminal_status == "failed"
    assert failed_frame.payload["evaluation_status"] == "nonphysical"
    assert failed_frame.payload["objective_value"] is None
    assert failed_frame.payload["failure_is_penalty_value"] is False
    assert all(metric.metric_id != "objective_value" for metric in failed_frame.metrics)
    assert build_failed_simulation_scenario(failure).purpose == "failure_contrast"
    assert build_failed_simulation_scenario(feasible).artifact.renderer_family == "generic_metric_history"


def test_ec027_links_its_own_failure_contrast() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "EC027")
    comparisons = load_comparison_seed(Path("data/seeds/site_comparisons.json"), "test")
    comparison = next(
        item
        for item in comparisons.comparisons
        if item.comparison_id == "COMPARE_FAILED_SIMULATION_STATUS_LEDGER"
    )

    assert FAILURE_SCENARIO_ID in case["visualization_ids"]
    assert case["comparison_ids"] == ["COMPARE_FAILED_SIMULATION_STATUS_LEDGER"]
    assert comparison.problem_instance_id == PROBLEM_INSTANCE_ID
    assert comparison.ranking_eligible is False


def test_failed_simulation_evaluator_does_not_assign_a_failure_penalty() -> None:
    problem = get_runtime_problem(PROBLEM_INSTANCE_ID)

    assert problem.objective_value([0.65, 0.35, 0.0]) == pytest.approx(0.0)
    with pytest.raises(ValueError, match="implicit_failure"):
        problem.objective_value([0.1, 0.08, 0.0])
