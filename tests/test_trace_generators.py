import json
from pathlib import Path

import pytest

from optimization_compass.dataset_release import TARGET_DATASET_VERSION
from optimization_compass.trace_models import canonical_trace_bytes
from optimization_compass.traces import (
    generate_gradient_bundle,
    generate_gradient_trace,
    generate_nelder_mead_trace,
)

ROOT = Path(__file__).parents[1]


def test_nelder_mead_trace_is_deterministic_and_full_snapshot() -> None:
    first = generate_nelder_mead_trace(
        dataset_version=TARGET_DATASET_VERSION,
        problem_instance_id="OBJECTIVE_ROSENBROCK_2D",
    )
    second = generate_nelder_mead_trace(
        dataset_version=TARGET_DATASET_VERSION,
        problem_instance_id="OBJECTIVE_ROSENBROCK_2D",
    )
    assert canonical_trace_bytes(first) == canonical_trace_bytes(second)
    assert {frame.event_type for frame in first.frames} >= {"initialize", "order", "stop"}
    assert all(frame.points for frame in first.frames)
    assert first.frames[-1].oracle_evaluations <= first.evaluation_budget
    assert first.contract_version == "1.0.0"
    assert all(any(point.role == "centroid" for point in frame.points) for frame in first.frames)
    movement_vectors = [vector for frame in first.frames for vector in frame.vectors]
    assert movement_vectors
    assert any(
        any(component != 0 for component in vector.components) for vector in movement_vectors
    )


def test_canonical_nelder_mead_traces_match_atlas_scenario_contracts() -> None:
    payload = json.loads((ROOT / "data/seeds/atlas_metadata.json").read_text(encoding="utf-8"))
    seeds = {
        item["scenario_id"]: item
        for item in payload["demo_scenarios"]
        if item["scenario_id"] in {"SCENARIO_NM_QUADRATIC", "SCENARIO_NM_ROSENBROCK"}
    }

    for scenario_id, seed in seeds.items():
        trace = generate_nelder_mead_trace(
            dataset_version=TARGET_DATASET_VERSION,
            problem_instance_id=seed["problem_instance_id"],
        )
        assert trace.scenario_id == scenario_id
        assert trace.initial_state["point"] == seed["initial_point"]
        assert trace.evaluation_budget == seed["budget"]
        assert trace.stopping == seed["stopping"]
        assert all(trace.parameters[key] == value for key, value in seed["parameters"].items())


@pytest.mark.parametrize(
    ("initial_point", "initial_scale", "budget"),
    [(None, None, None), ([-2.0, -1.0], 0.8, 80)],
)
def test_rosenbrock_initial_simplex_stays_inside_display_range(
    initial_point: list[float] | None,
    initial_scale: float | None,
    budget: int | None,
) -> None:
    trace = generate_nelder_mead_trace(
        dataset_version=TARGET_DATASET_VERSION,
        problem_instance_id="OBJECTIVE_ROSENBROCK_2D",
        initial_point=initial_point,
        initial_scale=initial_scale,
        budget=budget,
    )
    display_range = trace.objective["display_range"]

    assert all(
        display_range["x"][0] <= point[0] <= display_range["x"][1]
        and display_range["y"][0] <= point[1] <= display_range["y"][1]
        for point in trace.initial_state["simplex"]
    )


def test_nelder_mead_rejects_nonpositive_initial_scale() -> None:
    with pytest.raises(ValueError, match="initial scale must be positive"):
        generate_nelder_mead_trace(
            dataset_version=TARGET_DATASET_VERSION,
            initial_scale=0.0,
        )


def test_nelder_mead_rejected_candidate_is_preserved_for_shrink_explanation() -> None:
    trace = generate_nelder_mead_trace(
        dataset_version=TARGET_DATASET_VERSION,
        problem_instance_id="OBJECTIVE_ROSENBROCK_2D",
        initial_point=[-2.0, -1.0],
        initial_scale=0.8,
        budget=80,
    )
    rejected = [frame for frame in trace.frames if frame.decision == "rejected"]

    assert rejected
    assert all(any(point.role == "trial-point" for point in frame.points) for frame in rejected)


def test_gradient_bundle_shares_fairness_contract_and_has_three_methods() -> None:
    bundle = generate_gradient_bundle(dataset_version=TARGET_DATASET_VERSION)
    assert [trace.method_id for trace in bundle.member_traces] == [
        "M_GRADIENT_DESCENT",
        "M_MOMENTUM_SGD",
        "M_ADAM",
    ]
    assert all(trace.objective == bundle.objective for trace in bundle.member_traces)
    assert all(trace.initial_state == bundle.initial_state for trace in bundle.member_traces)
    assert all(
        trace.evaluation_budget == bundle.evaluation_budget for trace in bundle.member_traces
    )


def test_gradient_trace_stops_safely_when_learning_rate_diverges() -> None:
    trace = generate_gradient_trace(
        "gradient_descent",
        dataset_version=TARGET_DATASET_VERSION,
        parameters={"learning_rate": 0.1},
    )
    assert trace.terminal_status == "diverged"
    assert trace.frames[-1].event_type == "stop"
    assert trace.frames[-1].metrics[0].value < 1e12


def test_gradient_failure_preset_keeps_contract_and_exposes_both_vectors() -> None:
    bundle = generate_gradient_bundle(
        dataset_version=TARGET_DATASET_VERSION,
        preset="divergence",
    )

    assert bundle.contract_version == "1.0.0"
    assert bundle.comparison_id == "COMPARE_GRADIENT_DIVERGENCE"
    assert any(trace.terminal_status == "diverged" for trace in bundle.member_traces)
    for trace in bundle.member_traces:
        update_frames = [frame for frame in trace.frames if frame.event_type == "update"]
        assert update_frames
        assert all(
            {vector.role for vector in frame.vectors} == {"gradient", "movement"}
            for frame in update_frames
        )
