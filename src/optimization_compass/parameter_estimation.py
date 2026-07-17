from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from optimization_compass.problem_registry import (
    RuntimeProblem,
    exponential_decay_jacobian,
    exponential_decay_residuals,
    get_runtime_problem,
)
from optimization_compass.trace_models import (
    AlgorithmTrace,
    TerminalStatus,
    TraceFrame,
    TraceMetric,
    TracePoint,
)

PROBLEM_INSTANCE_ID = "INSTANCE_EXPONENTIAL_DECAY_FIT_3P"
PRIMARY_SCENARIO_ID = "SCENARIO_EXPONENTIAL_FIT_TRF"
POOR_INITIALIZATION_SCENARIO_ID = "SCENARIO_EXPONENTIAL_FIT_TRF_POOR_INIT"
LM_SCENARIO_ID = "SCENARIO_EXPONENTIAL_FIT_LM"
LBFGSB_SCENARIO_ID = "SCENARIO_EXPONENTIAL_FIT_LBFGSB"
NORMAL_INITIAL_POINT = [1.0, 0.4, 0.0]
POOR_INITIAL_POINT = [0.0, 2.5, 0.25]
TRUTH = [1.8, 0.7, 0.25]
LOWER_BOUNDS = [0.0, 0.0, -1.0]
UPPER_BOUNDS = [5.0, 3.0, 2.0]
EVALUATION_BUDGET = 12
RESIDUAL_NORM_TOLERANCE = 1e-6
GRADIENT_NORM_TOLERANCE = 1e-6
PROBE_DAMPING = 0.25
PROBE_STEP_RADIUS = 0.5


@dataclass(frozen=True)
class TracePreset:
    trace_id: str
    scenario_id: str
    method_id: str
    profile_id: str
    condition_ja: str
    condition_en: str
    initial_point: list[float]
    source_ids: list[str]


def generate_parameter_estimation_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    """Build solver-independent diagnostic probes for three applicability lenses.

    The normal-initialization members deliberately receive byte-equivalent frame histories.
    Their labels describe solver applicability conditions, not executions of those solvers.
    """
    presets = [
        TracePreset(
            trace_id="exponential-fit-trf",
            scenario_id=PRIMARY_SCENARIO_ID,
            method_id="M_TRUST_REGION_REFLECTIVE",
            profile_id="PROFILE_TRF_RESIDUAL_HISTORY",
            condition_ja="TRFのbounds・残差vector利用条件",
            condition_en="TRF bounds and residual-vector applicability",
            initial_point=NORMAL_INITIAL_POINT,
            source_ids=["S003", "S056", "S096"],
        ),
        TracePreset(
            trace_id="exponential-fit-trf-poor-init",
            scenario_id=POOR_INITIALIZATION_SCENARIO_ID,
            method_id="M_TRUST_REGION_REFLECTIVE",
            profile_id="PROFILE_TRF_RESIDUAL_HISTORY",
            condition_ja="同じ診断probeの悪い初期値感度",
            condition_en="Poor-start sensitivity of the same diagnostic probe",
            initial_point=POOR_INITIAL_POINT,
            source_ids=["S003", "S056", "S096"],
        ),
        TracePreset(
            trace_id="exponential-fit-lm",
            scenario_id=LM_SCENARIO_ID,
            method_id="M_LEVENBERG_MARQUARDT",
            profile_id="PROFILE_LM_RESIDUAL_HISTORY",
            condition_ja="LMのbounds非active適用条件",
            condition_en="LM applicability when bounds remain inactive",
            initial_point=NORMAL_INITIAL_POINT,
            source_ids=["S003", "S041", "S056"],
        ),
        TracePreset(
            trace_id="exponential-fit-lbfgsb",
            scenario_id=LBFGSB_SCENARIO_ID,
            method_id="M_LBFGSB",
            profile_id="PROFILE_LBFGSB_SCALAR_HISTORY",
            condition_ja="L-BFGS-Bのscalar目的fallback条件",
            condition_en="L-BFGS-B scalar-objective fallback applicability",
            initial_point=NORMAL_INITIAL_POINT,
            source_ids=["S002", "S056", "S065"],
        ),
    ]
    return [_generate_trace(dataset_version=dataset_version, preset=preset) for preset in presets]


def _generate_trace(*, dataset_version: str, preset: TracePreset) -> AlgorithmTrace:
    problem = get_runtime_problem(PROBLEM_INSTANCE_ID)
    stopping: dict[str, object] = {
        "max_oracle_evaluations": EVALUATION_BUDGET,
        "residual_norm_tolerance": RESIDUAL_NORM_TOLERANCE,
        "gradient_norm_tolerance": GRADIENT_NORM_TOLERANCE,
    }
    frames, terminal_status = _generate_probe_frames(problem, preset.initial_point, stopping)
    validate_stopping_consistency(frames, stopping, terminal_status)
    normal_context = preset.initial_point == NORMAL_INITIAL_POINT
    fairness = (
        "3 memberすべてに、同じ20観測・model・初期値 [1.0, 0.4, 0.0] と同じ"
        "solver-independent damped Gauss–Newton診断probeを表示します。差はsolverの適用条件"
        "annotationだけで、TRF・LM・L-BFGS-Bの実行結果や性能差ではありません。"
        if normal_context
        else (
            "通常初期値との感度確認として、同じ20観測・model・bounds・damped Gauss–Newton"
            "診断probeを初期値 [0.0, 2.5, 0.25] から開始します。TRFの実行結果ではありません。"
        )
    )
    reached_tolerance = terminal_status == "converged"
    terminal_summary_ja = (
        "solver-independent診断probeは記録した最終評価で停止criterionに到達しました。"
        if reached_tolerance
        else "solver-independent診断probeは停止criterion未達のまま12評価を使いました。"
    )
    terminal_summary_en = (
        "The solver-independent diagnostic probe reached a stopping criterion at its final "
        "recorded evaluation."
        if reached_tolerance
        else "The solver-independent diagnostic probe used 12 evaluations without meeting a "
        "stopping criterion."
    )
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=preset.trace_id,
        method_id=preset.method_id,
        profile_id=preset.profile_id,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=preset.scenario_id,
        generator_id="educational.exponential_decay_diagnostic_probe.v1",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective=problem.trace_objective(),
        preset={
            "preset_id": "PRESET_EXPONENTIAL_DECAY_20_POINT",
            "derivation_status": "deterministic_diagnostic_probe",
        },
        parameters={
            "model": "a*exp(-k*t)+c",
            "observation_count": 20,
            "truth": TRUTH,
            "lower_bounds": LOWER_BOUNDS,
            "upper_bounds": UPPER_BOUNDS,
            "probe_update_rule": "damped_gauss_newton",
            "probe_damping": PROBE_DAMPING,
            "probe_step_radius": PROBE_STEP_RADIUS,
            "solver_execution": False,
            "condition_lens": preset.condition_en,
            "condition_lens_ja": preset.condition_ja,
            "not_implementation_internals": True,
        },
        initial_state={"point": preset.initial_point, "parameter_names": ["a", "k", "c"]},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=EVALUATION_BUDGET,
        stopping=stopping,
        environment={"runtime": "deterministic_diagnostic_probe", "version": "1.0.0"},
        fairness_statement=fairness,
        frames=frames,
        terminal_status=terminal_status,
        terminal_summary_ja=terminal_summary_ja,
        terminal_summary_en=terminal_summary_en,
        source_ids=preset.source_ids,
    )


def _generate_probe_frames(
    problem: RuntimeProblem,
    initial_point: Sequence[float],
    stopping: Mapping[str, object],
) -> tuple[list[TraceFrame], TerminalStatus]:
    point = [float(value) for value in initial_point]
    frames: list[TraceFrame] = []
    terminal_status: TerminalStatus = "budget_exhausted"
    for frame_index in range(EVALUATION_BUDGET):
        frame = _frame(problem, point, frame_index=frame_index)
        frames.append(frame)
        if _meets_stopping_criterion(frame, stopping):
            terminal_status = "converged"
            break
        if frame.oracle_evaluations == EVALUATION_BUDGET:
            break
        point = _diagnostic_probe_update(problem, point)
    frames[-1] = frames[-1].model_copy(update={"keyframe": True})
    return frames, terminal_status


def _diagnostic_probe_update(problem: RuntimeProblem, point: Sequence[float]) -> list[float]:
    residuals = exponential_decay_residuals(problem.instance, point)
    jacobian = exponential_decay_jacobian(problem.instance, point)
    normal_matrix = [
        [sum(row[left] * row[right] for row in jacobian) for right in range(3)] for left in range(3)
    ]
    half_gradient = [
        sum(row[column] * residual for row, residual in zip(jacobian, residuals, strict=True))
        for column in range(3)
    ]
    for index in range(3):
        normal_matrix[index][index] += PROBE_DAMPING * max(normal_matrix[index][index], 1.0)
    step = _solve_linear_system(normal_matrix, [-value for value in half_gradient])
    step_norm = math.sqrt(sum(value * value for value in step))
    if step_norm > PROBE_STEP_RADIUS:
        step = [value * PROBE_STEP_RADIUS / step_norm for value in step]
    return [
        max(lower, min(upper, value + delta))
        for value, delta, lower, upper in zip(point, step, LOWER_BOUNDS, UPPER_BOUNDS, strict=True)
    ]


def _solve_linear_system(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    augmented = [list(row) + [float(value)] for row, value in zip(matrix, vector, strict=True)]
    size = len(vector)
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        diagonal = augmented[column][column]
        if abs(diagonal) <= 1e-14:
            raise ValueError("diagnostic probe normal matrix is singular after damping")
        for index in range(column, size + 1):
            augmented[column][index] /= diagonal
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            for index in range(column, size + 1):
                augmented[row][index] -= factor * augmented[column][index]
    return [augmented[row][size] for row in range(size)]


def validate_stopping_consistency(
    frames: Sequence[TraceFrame],
    stopping: Mapping[str, object],
    terminal_status: TerminalStatus,
) -> None:
    """Reject a trace that records updates after its first satisfied stop criterion."""
    first_stop = next(
        (index for index, frame in enumerate(frames) if _meets_stopping_criterion(frame, stopping)),
        None,
    )
    if first_stop is not None and first_stop != len(frames) - 1:
        raise ValueError("parameter-estimation trace contains frames after a stopping criterion")
    if first_stop is not None and terminal_status != "converged":
        raise ValueError("a satisfied stopping criterion requires converged terminal status")
    if first_stop is None and terminal_status == "converged":
        raise ValueError("converged terminal status requires a satisfied stopping criterion")


def _meets_stopping_criterion(frame: TraceFrame, stopping: Mapping[str, object]) -> bool:
    metrics = {metric.metric_id: metric.value for metric in frame.metrics}
    residual_tolerance = stopping.get("residual_norm_tolerance")
    gradient_tolerance = stopping.get("gradient_norm_tolerance")
    residual_met = isinstance(residual_tolerance, (int, float)) and metrics[
        "residual_norm"
    ] <= float(residual_tolerance)
    gradient_met = isinstance(gradient_tolerance, (int, float)) and metrics[
        "gradient_norm"
    ] <= float(gradient_tolerance)
    return residual_met or gradient_met


def _frame(problem: RuntimeProblem, point: list[float], *, frame_index: int) -> TraceFrame:
    residuals = exponential_decay_residuals(problem.instance, point)
    jacobian = exponential_decay_jacobian(problem.instance, point)
    objective = sum(value * value for value in residuals)
    gradient = problem.objective_gradient(point)
    residual_norm = math.sqrt(objective)
    gradient_norm = math.sqrt(sum(value * value for value in gradient))
    parameter_error = math.dist(point, TRUTH)
    return TraceFrame(
        frame_index=frame_index,
        iteration=frame_index,
        oracle_evaluations=frame_index + 1,
        elapsed_steps=frame_index,
        elapsed_time_ms=float(frame_index * 100),
        event_type="initialize" if frame_index == 0 else "diagnostic_probe_update",
        decision="not_applicable" if frame_index == 0 else "accepted",
        explanation_key="shared_diagnostic_probe",
        event_label_ja=(
            "初期parameterを診断" if frame_index == 0 else "共通damped Gauss–Newton診断probe"
        ),
        event_label_en=(
            "Diagnose initial parameters"
            if frame_index == 0
            else "Shared damped Gauss-Newton diagnostic probe"
        ),
        keyframe=frame_index == 0,
        points=[
            TracePoint(
                point_id="parameters",
                role="parameter-estimate",
                coordinates=point,
                value=objective,
                label_ja="診断probe parameter [a, k, c]",
                label_en="diagnostic-probe parameters [a, k, c]",
            )
        ],
        vectors=[],
        metrics=[
            TraceMetric(
                metric_id="residual_norm",
                label_ja="残差norm",
                label_en="Residual norm",
                value=residual_norm,
                unit="response",
            ),
            TraceMetric(
                metric_id="gradient_norm",
                label_ja="scalar目的のgradient norm",
                label_en="Scalar-objective gradient norm",
                value=gradient_norm,
                unit="objective/parameter",
            ),
            TraceMetric(
                metric_id="jacobian_rank",
                label_ja="Jacobian rank",
                label_en="Jacobian rank",
                value=float(_matrix_rank(jacobian)),
                unit="rank",
            ),
            TraceMetric(
                metric_id="parameter_error",
                label_ja="既知truthからの距離",
                label_en="Distance from known truth",
                value=parameter_error,
                unit="parameter distance",
            ),
        ],
        payload={
            "derivation_status": "deterministic_diagnostic_probe",
            "update_rule": "damped_gauss_newton",
            "residual_count": len(residuals),
            "solver_execution": False,
            "not_scipy_or_ceres_internal_iterations": True,
        },
    )


def _matrix_rank(rows: Sequence[Sequence[float]]) -> int:
    """Small deterministic modified Gram-Schmidt rank for the 20-by-3 Jacobian."""
    columns = [list(column) for column in zip(*rows, strict=True)]
    basis: list[list[float]] = []
    for column in columns:
        vector = column[:]
        scale = math.sqrt(sum(value * value for value in column))
        for unit in basis:
            projection = sum(
                value * direction for value, direction in zip(vector, unit, strict=True)
            )
            vector = [
                value - projection * direction
                for value, direction in zip(vector, unit, strict=True)
            ]
        norm = math.sqrt(sum(value * value for value in vector))
        if norm > max(1e-12, scale * 1e-10):
            basis.append([value / norm for value in vector])
    return len(basis)
