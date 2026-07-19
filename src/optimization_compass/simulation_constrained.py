from __future__ import annotations

from typing import Literal

from optimization_compass.trace_models import AlgorithmTrace, TraceFrame, TraceMetric, TracePoint

PROBLEM_DEFINITION_ID = "PROBLEM_TOPOLOGY_OPTIMIZATION"
PROBLEM_INSTANCE_ID = "INSTANCE_TOPOLOGY_CANTILEVER_2D"
PROFILE_ID = "PROFILE_SIMULATION_CONSTRAINED_LEDGER"

TIGHT_SCENARIO_ID = "SCENARIO_PDE_STATE_TOLERANCE_TIGHT"
LOOSE_SCENARIO_ID = "SCENARIO_PDE_STATE_TOLERANCE_LOOSE"
FAILURE_SCENARIO_ID = "SCENARIO_PDE_STATE_SOLVE_FAILURE"

TIGHT_TRACE_ID = "pde-state-tolerance-tight"
LOOSE_TRACE_ID = "pde-state-tolerance-loose"
FAILURE_TRACE_ID = "pde-state-solve-failure"

StatePolicy = Literal["tight", "loose", "failure"]
FrameValue = tuple[
    float | None,
    float,
    float,
    int,
    int,
    Literal["converged", "diverged_pc_failed"],
]


def _metric(metric_id: str, label_ja: str, label_en: str, value: float, unit: str) -> TraceMetric:
    return TraceMetric(
        metric_id=metric_id,
        label_ja=label_ja,
        label_en=label_en,
        value=value,
        unit=unit,
    )


def _frame(
    *,
    index: int,
    objective: float | None,
    state_residual: float,
    adjoint_residual: float,
    state_iterations: int,
    adjoint_iterations: int,
    status: Literal["converged", "diverged_pc_failed"],
) -> TraceFrame:
    metrics = [
        _metric("state_residual", "state残差", "state residual", state_residual, "residual"),
        _metric(
            "adjoint_residual",
            "adjoint残差",
            "adjoint residual",
            adjoint_residual,
            "residual",
        ),
        _metric(
            "state_linear_iterations",
            "state線形反復",
            "state linear iterations",
            float(state_iterations),
            "iterations",
        ),
        _metric(
            "adjoint_linear_iterations",
            "adjoint線形反復",
            "adjoint linear iterations",
            float(adjoint_iterations),
            "iterations",
        ),
    ]
    if objective is not None:
        metrics.insert(
            0,
            _metric(
                "objective_value",
                "離散objective",
                "discrete objective",
                objective,
                "normalized compliance",
            ),
        )
    return TraceFrame(
        frame_index=index,
        iteration=index,
        oracle_evaluations=index + 1,
        elapsed_steps=index,
        elapsed_time_ms=float((state_iterations + adjoint_iterations) * 10),
        event_type="state_solve_failed" if status != "converged" else "design_state_adjoint",
        decision="rejected" if status != "converged" else "accepted",
        explanation_key=f"simulation_constrained.{status}",
        event_label_ja=(
            "state solve失敗をfailed evaluationとして記録"
            if status != "converged"
            else "design更新・state solve・adjoint solveを記録"
        ),
        event_label_en=(
            "Record the state-solve failure as a failed evaluation"
            if status != "converged"
            else "Record the design update, state solve, and adjoint solve"
        ),
        keyframe=True,
        points=[
            TracePoint(
                point_id="design_state",
                role="decision",
                coordinates=[round(0.5 - 0.015 * index, 6), state_residual],
                value=objective,
                label_ja="設計変数とstate残差",
                label_en="design variable and state residual",
            )
        ],
        vectors=[],
        metrics=metrics,
        payload={
            "evaluation_status": status,
            "objective_value": objective,
            "state_residual": state_residual,
            "adjoint_residual": adjoint_residual,
            "state_linear_iterations": state_iterations,
            "adjoint_linear_iterations": adjoint_iterations,
            "failure_is_penalty_value": False,
        },
    )


def _trace(*, dataset_version: str, policy: StatePolicy) -> AlgorithmTrace:
    values: list[FrameValue]
    terminal_status: Literal["converged", "completed", "failed"]
    if policy == "tight":
        values = [
            (1.00, 8e-9, 7e-9, 34, 29, "converged"),
            (0.86, 7e-9, 7e-9, 35, 30, "converged"),
            (0.76, 7e-9, 6e-9, 37, 31, "converged"),
            (0.69, 6e-9, 6e-9, 38, 32, "converged"),
            (0.64, 6e-9, 5e-9, 39, 33, "converged"),
            (0.61, 5e-9, 5e-9, 41, 34, "converged"),
        ]
        scenario_id = TIGHT_SCENARIO_ID
        trace_id = TIGHT_TRACE_ID
        tolerance = 1e-8
        terminal_status = "converged"
        summary_ja = "tight toleranceではstate/adjoint残差を保つ代わりに線形反復costが増えました。"
        summary_en = (
            "The tight tolerance preserves state and adjoint residuals at higher linear-solve cost."
        )
    elif policy == "loose":
        values = [
            (1.00, 8e-4, 7e-4, 10, 9, "converged"),
            (0.84, 9e-4, 8e-4, 10, 9, "converged"),
            (0.71, 1.1e-3, 9e-4, 11, 9, "converged"),
            (0.62, 1.4e-3, 1.2e-3, 11, 10, "converged"),
            (0.55, 1.8e-3, 1.5e-3, 12, 10, "converged"),
            (0.51, 2.2e-3, 1.9e-3, 12, 11, "converged"),
        ]
        scenario_id = LOOSE_SCENARIO_ID
        trace_id = LOOSE_TRACE_ID
        tolerance = 1e-3
        terminal_status = "completed"
        summary_ja = (
            "loose toleranceは反復costを下げましたが、離散objectiveの改善と"
            "state/adjoint整合性を同一視できません。"
        )
        summary_en = (
            "The loose tolerance reduces iteration cost, but discrete-objective "
            "progress is not state/adjoint consistency."
        )
    else:
        values = [
            (1.00, 8e-7, 7e-7, 20, 18, "converged"),
            (0.87, 9e-7, 8e-7, 22, 19, "converged"),
            (0.78, 1.2e-6, 1.0e-6, 25, 21, "converged"),
            (None, 4.8e-1, 3.6e-1, 50, 0, "diverged_pc_failed"),
        ]
        scenario_id = FAILURE_SCENARIO_ID
        trace_id = FAILURE_TRACE_ID
        tolerance = 1e-6
        terminal_status = "failed"
        summary_ja = (
            "preconditioner failureを目的値のpenaltyへ変換せず、"
            "failed evaluationとして停止しました。"
        )
        summary_en = (
            "The preconditioner failure remains a failed evaluation rather than an "
            "objective penalty."
        )
    frames = [
        _frame(
            index=index,
            objective=objective,
            state_residual=state_residual,
            adjoint_residual=adjoint_residual,
            state_iterations=state_iterations,
            adjoint_iterations=adjoint_iterations,
            status=status,
        )
        for index, (
            objective,
            state_residual,
            adjoint_residual,
            state_iterations,
            adjoint_iterations,
            status,
        ) in enumerate(values)
    ]
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id,
        method_id="M_ADJOINT_SENSITIVITY",
        profile_id=PROFILE_ID,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=scenario_id,
        generator_id="educational.simulation_constrained.v1",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"kind": "discrete_compliance", "direction": "minimize"},
        preset={"preset_id": scenario_id.removeprefix("SCENARIO_")},
        parameters={
            "formulation": "reduced_space",
            "state_tolerance": tolerance,
            "adjoint_tolerance": tolerance,
            "failure_policy": "explicit_failed_evaluation_no_penalty",
            "discretization": "fixed_8x4_teaching_mesh",
        },
        initial_state={"point": [0.5, 0.0], "design_dimension": 32},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=len(frames),
        stopping={"state_solve_calls": len(frames), "state_tolerance": tolerance},
        environment={"runtime": "deterministic_teaching_ledger", "version": "1.0.0"},
        fairness_statement=(
            "The same topology instance, mesh, initial density, design updates, preconditioner "
            "policy, call budget, and failure mapping are used; only state/adjoint "
            "tolerance changes."
        ),
        frames=frames,
        terminal_status=terminal_status,
        terminal_summary_ja=summary_ja,
        terminal_summary_en=summary_en,
        source_ids=["S019", "S097", "S101", "S110"],
    )


def generate_simulation_constrained_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    return [
        _trace(dataset_version=dataset_version, policy="tight"),
        _trace(dataset_version=dataset_version, policy="loose"),
        _trace(dataset_version=dataset_version, policy="failure"),
    ]
