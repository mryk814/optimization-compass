from __future__ import annotations

import math
from collections.abc import Sequence
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
EVALUATION_BUDGET = 12


@dataclass(frozen=True)
class TracePreset:
    trace_id: str
    scenario_id: str
    method_id: str
    profile_id: str
    label_ja: str
    label_en: str
    initial_point: list[float]
    progress: tuple[float, ...]
    source_ids: list[str]
    terminal_status: TerminalStatus
    terminal_summary_ja: str
    terminal_summary_en: str


def generate_parameter_estimation_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    """Build deterministic teaching paths, not implementation-internal solver iterations."""
    presets = [
        TracePreset(
            trace_id="exponential-fit-trf",
            scenario_id=PRIMARY_SCENARIO_ID,
            method_id="M_TRUST_REGION_REFLECTIVE",
            profile_id="PROFILE_TRF_RESIDUAL_HISTORY",
            label_ja="TRFのbounds付き残差fit",
            label_en="Bounded residual fitting with TRF",
            initial_point=NORMAL_INITIAL_POINT,
            progress=(0.0, 0.15, 0.32, 0.50, 0.66, 0.78, 0.87, 0.93, 0.97, 0.99, 0.998, 1.0),
            source_ids=["S003", "S056", "S096"],
            terminal_status="converged",
            terminal_summary_ja="固定教材pathは既知parameterへ到達しました。TRF実装の内部反復ではありません。",
            terminal_summary_en=(
                "The fixed teaching path reached the known parameters; it is not a trace "
                "of TRF implementation internals."
            ),
        ),
        TracePreset(
            trace_id="exponential-fit-trf-poor-init",
            scenario_id=POOR_INITIALIZATION_SCENARIO_ID,
            method_id="M_TRUST_REGION_REFLECTIVE",
            profile_id="PROFILE_TRF_RESIDUAL_HISTORY",
            label_ja="TRFの悪い初期値感度",
            label_en="TRF poor-initialization sensitivity",
            initial_point=POOR_INITIAL_POINT,
            progress=(0.0, 0.01, 0.03, 0.06, 0.10, 0.16, 0.24, 0.33, 0.43, 0.54, 0.65, 0.75),
            source_ids=["S003", "S056", "S096"],
            terminal_status="budget_exhausted",
            terminal_summary_ja=(
                "rankが落ちた初期点では12評価後も残差が残ります。初期値感度を示す教材pathです。"
            ),
            terminal_summary_en=(
                "The rank-deficient start retains residual error after 12 evaluations; "
                "this is an initialization-sensitivity teaching path."
            ),
        ),
        TracePreset(
            trace_id="exponential-fit-lm",
            scenario_id=LM_SCENARIO_ID,
            method_id="M_LEVENBERG_MARQUARDT",
            profile_id="PROFILE_LM_RESIDUAL_HISTORY",
            label_ja="LMのbounds非active条件",
            label_en="LM when bounds remain inactive",
            initial_point=NORMAL_INITIAL_POINT,
            progress=(0.0, 0.25, 0.48, 0.68, 0.83, 0.92, 0.97, 0.99, 0.997, 1.0, 1.0, 1.0),
            source_ids=["S003", "S041", "S056"],
            terminal_status="converged",
            terminal_summary_ja=(
                "固定pathではboundsを踏まず収束しましたが、LMがboundsを直接扱えるという意味ではありません。"
            ),
            terminal_summary_en=(
                "The fixed path converged without touching a bound; this does not mean "
                "that LM directly supports bounds."
            ),
        ),
        TracePreset(
            trace_id="exponential-fit-lbfgsb",
            scenario_id=LBFGSB_SCENARIO_ID,
            method_id="M_LBFGSB",
            profile_id="PROFILE_LBFGSB_SCALAR_HISTORY",
            label_ja="L-BFGS-Bのscalar目的fallback",
            label_en="L-BFGS-B scalar-objective fallback",
            initial_point=NORMAL_INITIAL_POINT,
            progress=(0.0, 0.08, 0.18, 0.29, 0.41, 0.53, 0.64, 0.74, 0.82, 0.88, 0.93, 0.96),
            source_ids=["S002", "S056", "S065"],
            terminal_status="budget_exhausted",
            terminal_summary_ja=(
                "scalar二乗和fallbackは残差構造の専用診断を使わず、12評価で誤差を残しました。"
            ),
            terminal_summary_en=(
                "The scalar sum-of-squares fallback leaves error after 12 evaluations "
                "without residual-specific solver diagnostics."
            ),
        ),
    ]
    return [_generate_trace(dataset_version=dataset_version, preset=preset) for preset in presets]


def _generate_trace(*, dataset_version: str, preset: TracePreset) -> AlgorithmTrace:
    if len(preset.progress) != EVALUATION_BUDGET:
        raise ValueError("parameter-estimation teaching paths must have 12 evaluations")
    problem = get_runtime_problem(PROBLEM_INSTANCE_ID)
    points = [_interpolate(preset.initial_point, TRUTH, fraction) for fraction in preset.progress]
    frames = [
        _frame(
            problem, point, frame_index=index, label_ja=preset.label_ja, label_en=preset.label_en
        )
        for index, point in enumerate(points)
    ]
    fairness = (
        "同じ20観測・model・初期値 [1.0, 0.4, 0.0]・12 oracle evaluationで読む教育用pathです。"
        "SciPyまたはCeresの内部反復や一般性能を再現しません。"
        if preset.initial_point == NORMAL_INITIAL_POINT
        else (
            "同じ20観測・model・12 oracle evaluationで初期値だけを [0.0, 2.5, 0.25] "
            "へ変えた感度教材です。実装内部を再現しません。"
        )
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
        generator_id="educational.exponential_decay_fit.v1",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective=problem.trace_objective(),
        preset={
            "preset_id": "PRESET_EXPONENTIAL_DECAY_20_POINT",
            "derivation_status": "educational_path",
        },
        parameters={
            "model": "a*exp(-k*t)+c",
            "observation_count": 20,
            "truth": TRUTH,
            "lower_bounds": [0.0, 0.0, -1.0],
            "upper_bounds": [5.0, 3.0, 2.0],
            "not_implementation_internals": True,
        },
        initial_state={"point": preset.initial_point, "parameter_names": ["a", "k", "c"]},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=EVALUATION_BUDGET,
        stopping={
            "max_oracle_evaluations": EVALUATION_BUDGET,
            "residual_norm_tolerance": 1e-6,
            "gradient_norm_tolerance": 1e-6,
        },
        environment={"runtime": "deterministic_educational_path", "version": "1.0.0"},
        fairness_statement=fairness,
        frames=frames,
        terminal_status=preset.terminal_status,
        terminal_summary_ja=preset.terminal_summary_ja,
        terminal_summary_en=preset.terminal_summary_en,
        source_ids=preset.source_ids,
    )


def _frame(
    problem: RuntimeProblem,
    point: list[float],
    *,
    frame_index: int,
    label_ja: str,
    label_en: str,
) -> TraceFrame:
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
        event_type="initialize" if frame_index == 0 else "parameter_update",
        decision="not_applicable" if frame_index == 0 else "accepted",
        explanation_key="parameter_estimate",
        event_label_ja="初期parameter" if frame_index == 0 else f"{label_ja} · 教材update",
        event_label_en="Initial parameters"
        if frame_index == 0
        else f"{label_en} · teaching update",
        keyframe=frame_index in {0, EVALUATION_BUDGET - 1},
        points=[
            TracePoint(
                point_id="parameters",
                role="parameter-estimate",
                coordinates=point,
                value=objective,
                label_ja="parameter推定値 [a, k, c]",
                label_en="parameter estimate [a, k, c]",
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
            "derivation_status": "educational_path",
            "residual_count": len(residuals),
            "not_scipy_or_ceres_internal_iterations": True,
        },
    )


def _interpolate(start: Sequence[float], end: Sequence[float], fraction: float) -> list[float]:
    return [float(left + fraction * (right - left)) for left, right in zip(start, end, strict=True)]


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
