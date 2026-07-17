from __future__ import annotations

import pytest

from optimization_compass.parameter_estimation import (
    EVALUATION_BUDGET,
    LBFGSB_SCENARIO_ID,
    LM_SCENARIO_ID,
    NORMAL_INITIAL_POINT,
    POOR_INITIALIZATION_SCENARIO_ID,
    PRIMARY_SCENARIO_ID,
    generate_parameter_estimation_traces,
    validate_stopping_consistency,
)
from optimization_compass.problem_registry import get_runtime_problem
from optimization_compass.visualization_scenarios import scenario_identity


def test_exponential_decay_instance_exposes_residual_objective_and_gradient() -> None:
    problem = get_runtime_problem("INSTANCE_EXPONENTIAL_DECAY_FIT_3P")

    assert problem.definition.problem_definition_id == "PROBLEM_NONLINEAR_LEAST_SQUARES"
    assert problem.instance.registry_key == "problem.nonlinear_least_squares.exponential_decay.v1"
    assert problem.objective_value([1.8, 0.7, 0.25]) == pytest.approx(0.0, abs=1e-14)
    assert problem.objective_value(NORMAL_INITIAL_POINT) > 0
    assert problem.objective_gradient([1.8, 0.7, 0.25]) == pytest.approx([0.0, 0.0, 0.0])


def test_parameter_estimation_traces_share_context_and_keep_educational_semantics() -> None:
    traces = generate_parameter_estimation_traces(dataset_version="0.12.0")
    by_scenario = {trace.scenario_id: trace for trace in traces}

    assert set(by_scenario) == {
        PRIMARY_SCENARIO_ID,
        POOR_INITIALIZATION_SCENARIO_ID,
        LM_SCENARIO_ID,
        LBFGSB_SCENARIO_ID,
    }
    assert all(trace.evaluation_budget == EVALUATION_BUDGET for trace in traces)
    assert all(len(trace.frames) == EVALUATION_BUDGET for trace in traces)
    assert all(trace.implementation_mapping_status == "not_applicable" for trace in traces)
    assert all(trace.implementation_id is None for trace in traces)
    assert all(trace.parameters["not_implementation_internals"] is True for trace in traces)
    assert all(trace.parameters["solver_execution"] is False for trace in traces)

    comparison_traces = [
        by_scenario[PRIMARY_SCENARIO_ID],
        by_scenario[LM_SCENARIO_ID],
        by_scenario[LBFGSB_SCENARIO_ID],
    ]
    assert all(trace.initial_state["point"] == NORMAL_INITIAL_POINT for trace in comparison_traces)
    assert len({trace.fairness_statement for trace in comparison_traces}) == 1
    assert len({str(trace.stopping) for trace in comparison_traces}) == 1
    assert len({trace.terminal_status for trace in comparison_traces}) == 1
    assert comparison_traces[0].frames == comparison_traces[1].frames
    assert comparison_traces[0].frames == comparison_traces[2].frames
    assert all(
        frame.payload["solver_execution"] is False
        for trace in comparison_traces
        for frame in trace.frames
    )

    poor = by_scenario[POOR_INITIALIZATION_SCENARIO_ID]
    initial_metrics = {metric.metric_id: metric.value for metric in poor.frames[0].metrics}
    final_metrics = {metric.metric_id: metric.value for metric in poor.frames[-1].metrics}
    assert initial_metrics["jacobian_rank"] == 2
    assert final_metrics["jacobian_rank"] == 3
    assert final_metrics["residual_norm"] > 0
    assert poor.terminal_status == "budget_exhausted"


def test_parameter_estimation_trace_rejects_frames_after_first_stop() -> None:
    trace = generate_parameter_estimation_traces(dataset_version="0.12.0")[0]
    stopping = {
        "residual_norm_tolerance": 1e9,
        "gradient_norm_tolerance": 1e9,
        "max_oracle_evaluations": EVALUATION_BUDGET,
    }

    with pytest.raises(ValueError, match="frames after a stopping criterion"):
        validate_stopping_consistency(trace.frames[:2], stopping, "converged")


def test_parameter_estimation_scenarios_do_not_expand_canonical_metadata_contract() -> None:
    for scenario_id in (
        PRIMARY_SCENARIO_ID,
        POOR_INITIALIZATION_SCENARIO_ID,
        LM_SCENARIO_ID,
        LBFGSB_SCENARIO_ID,
    ):
        assert scenario_identity(scenario_id) == ("generated_only", None)
