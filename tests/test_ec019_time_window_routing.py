from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.comparisons import load_comparison_seed
from optimization_compass.problem_registry import get_runtime_problem
from optimization_compass.time_window_routing import (
    FEASIBLE_SCENARIO_ID,
    FEASIBLE_TRACE_ID,
    PROBLEM_INSTANCE_ID,
    VIOLATION_SCENARIO_ID,
    VIOLATION_TRACE_ID,
    build_time_window_routing_scenario,
    generate_time_window_routing_traces,
)


def test_fixed_time_window_route_keeps_feasibility_separate_from_travel_time() -> None:
    feasible, violation = generate_time_window_routing_traces(dataset_version="test")

    assert feasible.trace_id == FEASIBLE_TRACE_ID
    assert violation.trace_id == VIOLATION_TRACE_ID
    assert feasible.objective_id == violation.objective_id == PROBLEM_INSTANCE_ID
    assert [frame.payload["current_stop"] for frame in feasible.frames] == [0, 1, 2, 3, 4, 0]
    assert feasible.frames[-1].metrics[3].value == violation.frames[-1].metrics[3].value == 21.0
    assert feasible.frames[4].metrics[2].value == 0.0
    assert violation.frames[4].metrics[2].value == 2.0
    assert feasible.terminal_status == "completed"
    assert violation.terminal_status == "failed"


def test_time_window_routing_scenarios_are_scope_limited_metric_history() -> None:
    feasible, violation = generate_time_window_routing_traces(dataset_version="test")
    feasible_scenario = build_time_window_routing_scenario(feasible)
    violation_scenario = build_time_window_routing_scenario(violation)

    assert {feasible_scenario.scenario_id, violation_scenario.scenario_id} == {
        FEASIBLE_SCENARIO_ID,
        VIOLATION_SCENARIO_ID,
    }
    assert feasible_scenario.purpose == "mechanism"
    assert violation_scenario.purpose == "failure_contrast"
    assert violation_scenario.lesson.failure_signals
    assert feasible_scenario.artifact.renderer_family == "generic_metric_history"
    assert "OR-Tools" in feasible_scenario.lesson.limitations_en


def test_ec019_connects_its_own_instance_scenarios_and_comparison() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "EC019")
    comparisons = load_comparison_seed(Path("data/seeds/site_comparisons.json"), "test")
    comparison = next(
        item
        for item in comparisons.comparisons
        if item.comparison_id == "COMPARE_TIME_WINDOW_ROUTING_HARD_CONSTRAINT"
    )

    assert {FEASIBLE_SCENARIO_ID, VIOLATION_SCENARIO_ID} <= set(case["visualization_ids"])
    assert case["comparison_ids"] == ["COMPARE_TIME_WINDOW_ROUTING_HARD_CONSTRAINT"]
    assert comparison.problem_instance_id == PROBLEM_INSTANCE_ID
    assert comparison.changed_factors == ["stop 4の時間窓の終了だけを25分から12分へ狭める"]
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False


def test_registry_evaluates_the_fixed_route_as_travel_time() -> None:
    problem = get_runtime_problem(PROBLEM_INSTANCE_ID)

    assert problem.objective_value([1.0, 2.0, 3.0, 4.0]) == pytest.approx(21.0)
    with pytest.raises(ValueError, match="permutation"):
        problem.objective_value([1.0, 1.0, 3.0, 4.0])
