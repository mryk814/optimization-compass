from __future__ import annotations

import math
from hashlib import sha256
from typing import Literal

from optimization_compass.problem_registry import get_runtime_problem
from optimization_compass.trace_models import (
    AlgorithmTrace,
    TraceFrame,
    TraceMetric,
    TracePoint,
    canonical_trace_bytes,
)
from optimization_compass.visualization_scenarios import (
    KnownReferenceDisplay,
    LocalizedText,
    VisualizationArtifact,
    VisualizationBudget,
    VisualizationExperiment,
    VisualizationInitialCondition,
    VisualizationLesson,
    VisualizationNarrationStep,
    VisualizationObservable,
    VisualizationRun,
    VisualizationScenario,
    VisualizationSeed,
    VisualizationSignal,
    scenario_identity,
)

GENERATOR_ID = "educational.so3_attitude.v1"
GENERATOR_VERSION = "1.0.1"
TRACE_DECIMAL_PLACES = 12
PROFILE_ID = "PROFILE_SO3_ATTITUDE_ALIGNMENT"
PROBLEM_DEFINITION_ID = "PROBLEM_SO3_ATTITUDE_ALIGNMENT"
PROBLEM_INSTANCE_ID = "INSTANCE_SO3_ATTITUDE_FIXED_3"
PROJECTED_SCENARIO_ID = "SCENARIO_SO3_PROJECTED_ALIGNMENT"
RIEMANNIAN_SCENARIO_ID = "SCENARIO_SO3_RIEMANNIAN_ALIGNMENT"
PROJECTED_TRACE_ID = "so3-projected-alignment"
RIEMANNIAN_TRACE_ID = "so3-riemannian-alignment"
EVALUATION_BUDGET = 12

Strategy = Literal["projected", "riemannian"]
Matrix3 = tuple[float, float, float, float, float, float, float, float, float]
Vector3 = tuple[float, float, float]


def _localized(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def _matrix(value: object, owner: str) -> Matrix3:
    if not isinstance(value, list) or len(value) != 9:
        raise ValueError(f"{owner} must contain nine row-major values")
    numbers: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise ValueError(f"{owner} must contain only numeric values")
        numbers.append(float(item))
    return tuple(numbers)  # type: ignore[return-value]


def _identity() -> Matrix3:
    return (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def _transpose(matrix: Matrix3) -> Matrix3:
    return (
        matrix[0],
        matrix[3],
        matrix[6],
        matrix[1],
        matrix[4],
        matrix[7],
        matrix[2],
        matrix[5],
        matrix[8],
    )


def _multiply(left: Matrix3, right: Matrix3) -> Matrix3:
    return tuple(
        sum(left[3 * row + inner] * right[3 * inner + column] for inner in range(3))
        for row in range(3)
        for column in range(3)
    )  # type: ignore[return-value]


def _determinant(matrix: Matrix3) -> float:
    return (
        matrix[0] * (matrix[4] * matrix[8] - matrix[5] * matrix[7])
        - matrix[1] * (matrix[3] * matrix[8] - matrix[5] * matrix[6])
        + matrix[2] * (matrix[3] * matrix[7] - matrix[4] * matrix[6])
    )


def _frobenius(values: tuple[float, ...]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _subtract(left: Matrix3, right: Matrix3) -> Matrix3:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _objective(matrix: Matrix3, target: Matrix3) -> float:
    difference = _subtract(matrix, target)
    return 0.5 * sum(value * value for value in difference)


def _orthogonality_error(matrix: Matrix3) -> float:
    gram_error = _subtract(_multiply(_transpose(matrix), matrix), _identity())
    return _frobenius(gram_error)


def _dot(left: Vector3, right: Vector3) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _scale(vector: Vector3, factor: float) -> Vector3:
    return tuple(factor * value for value in vector)  # type: ignore[return-value]


def _subtract_vector(left: Vector3, right: Vector3) -> Vector3:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _normalize(vector: Vector3) -> Vector3:
    norm = math.sqrt(_dot(vector, vector))
    if norm <= 1e-12:
        raise ValueError("SO(3) projection encountered a degenerate column")
    return _scale(vector, 1.0 / norm)


def _cross(left: Vector3, right: Vector3) -> Vector3:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _column(matrix: Matrix3, index: int) -> Vector3:
    return (matrix[index], matrix[3 + index], matrix[6 + index])


def _from_columns(first: Vector3, second: Vector3, third: Vector3) -> Matrix3:
    return (
        first[0],
        second[0],
        third[0],
        first[1],
        second[1],
        third[1],
        first[2],
        second[2],
        third[2],
    )


def _qr_projection(matrix: Matrix3) -> Matrix3:
    first = _normalize(_column(matrix, 0))
    raw_second = _column(matrix, 1)
    second = _normalize(_subtract_vector(raw_second, _scale(first, _dot(first, raw_second))))
    third = _normalize(_cross(first, second))
    return _from_columns(first, second, third)


def _skew(vector: Vector3) -> Matrix3:
    x, y, z = vector
    return (0.0, -z, y, z, 0.0, -x, -y, x, 0.0)


def _matrix_add(left: Matrix3, right: Matrix3) -> Matrix3:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _matrix_scale(matrix: Matrix3, factor: float) -> Matrix3:
    return tuple(factor * value for value in matrix)  # type: ignore[return-value]


def _exponential(rotation_vector: Vector3) -> Matrix3:
    angle = math.sqrt(_dot(rotation_vector, rotation_vector))
    skew = _skew(rotation_vector)
    skew_squared = _multiply(skew, skew)
    if angle < 1e-8:
        sine_scale = 1.0 - angle * angle / 6.0
        cosine_scale = 0.5 - angle * angle / 24.0
    else:
        sine_scale = math.sin(angle) / angle
        cosine_scale = (1.0 - math.cos(angle)) / (angle * angle)
    return _matrix_add(
        _identity(),
        _matrix_add(_matrix_scale(skew, sine_scale), _matrix_scale(skew_squared, cosine_scale)),
    )


def _log_vector(relative: Matrix3) -> Vector3:
    cosine = max(-1.0, min(1.0, (relative[0] + relative[4] + relative[8] - 1.0) / 2.0))
    angle = math.acos(cosine)
    if angle < 1e-10:
        return (0.0, 0.0, 0.0)
    sine = math.sin(angle)
    if abs(sine) < 1e-6:
        raise ValueError("SO(3) logarithm is numerically ambiguous at pi")
    factor = angle / (2.0 * sine)
    return (
        factor * (relative[7] - relative[5]),
        factor * (relative[2] - relative[6]),
        factor * (relative[3] - relative[1]),
    )


def _geodesic_residual(matrix: Matrix3, target: Matrix3) -> float:
    relative = _multiply(_transpose(matrix), target)
    cosine = max(-1.0, min(1.0, (relative[0] + relative[4] + relative[8] - 1.0) / 2.0))
    return math.acos(cosine)


def _canonicalize_trace_value(value: float) -> float:
    """Remove platform libm drift at the educational-trace boundary."""
    return round(float(value), TRACE_DECIMAL_PLACES)


def _canonicalize_matrix(matrix: Matrix3) -> Matrix3:
    return tuple(_canonicalize_trace_value(value) for value in matrix)  # type: ignore[return-value]


def _metric(metric_id: str, ja: str, en: str, value: float, unit: str) -> TraceMetric:
    return TraceMetric(
        metric_id=metric_id,
        label_ja=ja,
        label_en=en,
        value=_canonicalize_trace_value(value),
        unit=unit,
    )


def _frame(
    *,
    index: int,
    strategy: Strategy,
    matrix: Matrix3,
    target: Matrix3,
    update_norm: float,
    map_correction_norm: float,
) -> TraceFrame:
    matrix = _canonicalize_matrix(matrix)
    objective = _canonicalize_trace_value(_objective(matrix, target))
    return TraceFrame(
        frame_index=index,
        iteration=index,
        oracle_evaluations=index,
        elapsed_steps=index,
        elapsed_time_ms=float(index),
        event_type="initialize" if index == 0 else "update",
        decision="not_applicable" if index == 0 else "accepted",
        explanation_key=f"so3-{strategy}-{'start' if index == 0 else 'update'}",
        event_label_ja="初期rotation" if index == 0 else "SO(3)上の更新",
        event_label_en="Initial rotation" if index == 0 else "Update on SO(3)",
        keyframe=index in {0, 1, 4, EVALUATION_BUDGET},
        points=[
            TracePoint(
                point_id="rotation",
                role="current",
                coordinates=list(matrix),
                value=objective,
                label_ja="現在のrotation matrix",
                label_en="Current rotation matrix",
            )
        ],
        vectors=[],
        metrics=[
            _metric("objective_value", "目的関数値", "objective value", objective, "squared loss"),
            _metric(
                "geodesic_residual",
                "geodesic residual",
                "geodesic residual",
                _geodesic_residual(matrix, target),
                "radian",
            ),
            _metric(
                "orthogonality_error",
                "直交性残差",
                "orthogonality error",
                _orthogonality_error(matrix),
                "Frobenius norm",
            ),
            _metric(
                "determinant_error",
                "determinant残差",
                "determinant error",
                abs(_determinant(matrix) - 1.0),
                "absolute error",
            ),
        ],
        payload={
            "strategy": strategy,
            "matrix": list(matrix),
            "target_matrix": list(target),
            "update_norm": _canonicalize_trace_value(update_norm),
            "map_correction_norm": _canonicalize_trace_value(map_correction_norm),
            "claim_scope": "fixed_three_correspondence_teaching_instance",
        },
    )


def generate_so3_trace(*, dataset_version: str, strategy: Strategy) -> AlgorithmTrace:
    problem = get_runtime_problem(PROBLEM_INSTANCE_ID)
    target = _matrix(problem.instance.parameters.get("target_rotation"), "target_rotation")
    initial = _matrix(problem.instance.parameters.get("initial_rotation"), "initial_rotation")
    step_size_value = problem.instance.parameters.get("step_size")
    if isinstance(step_size_value, bool) or not isinstance(step_size_value, int | float):
        raise ValueError("step_size must be numeric")
    step_size = float(step_size_value)
    matrix = initial
    frames = [
        _frame(
            index=0,
            strategy=strategy,
            matrix=matrix,
            target=target,
            update_norm=0.0,
            map_correction_norm=0.0,
        )
    ]
    for index in range(1, EVALUATION_BUDGET + 1):
        if strategy == "projected":
            ambient_step = _matrix_scale(_subtract(target, matrix), step_size)
            candidate = _matrix_add(matrix, ambient_step)
            next_matrix = _canonicalize_matrix(_qr_projection(candidate))
            update_norm = _canonicalize_trace_value(_frobenius(ambient_step))
            map_correction_norm = _canonicalize_trace_value(
                _frobenius(_subtract(next_matrix, candidate))
            )
        else:
            tangent = _log_vector(_multiply(_transpose(matrix), target))
            tangent_step = _scale(tangent, step_size)
            next_matrix = _canonicalize_matrix(_multiply(matrix, _exponential(tangent_step)))
            update_norm = _canonicalize_trace_value(math.sqrt(_dot(tangent_step, tangent_step)))
            first_order = _matrix_add(matrix, _multiply(matrix, _skew(tangent_step)))
            map_correction_norm = _canonicalize_trace_value(
                _frobenius(_subtract(next_matrix, first_order))
            )
        matrix = next_matrix
        frames.append(
            _frame(
                index=index,
                strategy=strategy,
                matrix=matrix,
                target=target,
                update_norm=update_norm,
                map_correction_norm=map_correction_norm,
            )
        )
    is_projected = strategy == "projected"
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=PROJECTED_TRACE_ID if is_projected else RIEMANNIAN_TRACE_ID,
        method_id="M_PROJECTED_GRADIENT" if is_projected else "M_RIEMANNIAN_GRADIENT",
        profile_id=PROFILE_ID,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=PROJECTED_SCENARIO_ID if is_projected else RIEMANNIAN_SCENARIO_ID,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective=problem.trace_objective(),
        preset={"preset_id": f"SO3_{strategy.upper()}_FIXED", "step_size": step_size},
        parameters={
            "strategy": strategy,
            "representation": "rotation_matrix",
            "feasibility_map": "qr_projection" if is_projected else "lie_exponential",
            "distance_diagnostic": "geodesic_angle",
            "numeric_canonicalization": (
                "round_half_even_12_decimal_places_after_each_update_and_before_export"
            ),
        },
        initial_state={"point": list(initial), "target_rotation": list(target)},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=EVALUATION_BUDGET,
        stopping={"max_oracle_evaluations": EVALUATION_BUDGET},
        environment={"runtime": "deterministic_educational", "version": GENERATOR_VERSION},
        fairness_statement=(
            "Both traces use the same target rotation, identity initialization, chordal "
            "objective, 0.35 step size, twelve updates, and diagnostics; only the feasibility "
            "strategy changes between ambient QR projection and a Lie-algebra exponential update."
        ),
        frames=frames,
        terminal_status="completed",
        terminal_summary_ja=(
            "固定されたnear-pi attitude alignmentを12 update実行し、"
            "目的関数とSO(3)構造残差を記録した。"
        ),
        terminal_summary_en=(
            "Twelve updates completed on the fixed near-pi attitude-alignment lesson while "
            "recording objective and SO(3) structure diagnostics."
        ),
        source_ids=["S044", "S045", "S071", "S107"],
    )


def generate_so3_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    return [
        generate_so3_trace(dataset_version=dataset_version, strategy="projected"),
        generate_so3_trace(dataset_version=dataset_version, strategy="riemannian"),
    ]


def build_so3_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    is_projected = trace.scenario_id == PROJECTED_SCENARIO_ID
    counterpart = RIEMANNIAN_SCENARIO_ID if is_projected else PROJECTED_SCENARIO_ID
    identity_status, canonical_scenario_id = scenario_identity(trace.scenario_id)
    raw_initial_point = trace.initial_state.get("point")
    if not isinstance(raw_initial_point, list) or not all(
        isinstance(value, int | float) and not isinstance(value, bool)
        for value in raw_initial_point
    ):
        raise ValueError("SO(3) trace initial point must be a numeric list")
    initial_point = [float(value) for value in raw_initial_point]
    payload = canonical_trace_bytes(trace)
    observables = [
        VisualizationObservable(
            observable_id="objective_value", label_ja="目的関数値", label_en="objective value"
        ),
        VisualizationObservable(
            observable_id="geodesic_residual",
            label_ja="geodesic residual",
            label_en="geodesic residual",
        ),
        VisualizationObservable(
            observable_id="orthogonality_error",
            label_ja="直交性残差",
            label_en="orthogonality error",
        ),
        VisualizationObservable(
            observable_id="determinant_error",
            label_ja="determinant残差",
            label_en="determinant error",
        ),
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status=identity_status,
        canonical_scenario_id=canonical_scenario_id,
        title_ja=(
            "ambient stepとQR projectionによるattitude alignment"
            if is_projected
            else "Lie algebra stepによるattitude alignment"
        ),
        title_en=(
            "Attitude alignment by ambient step and QR projection"
            if is_projected
            else "Attitude alignment by a Lie-algebra step"
        ),
        purpose="sensitivity" if is_projected else "mechanism",
        problem_definition_id=PROBLEM_DEFINITION_ID,
        problem_instance_id=PROBLEM_INSTANCE_ID,
        lesson=VisualizationLesson(
            learning_objective=_localized(
                "目的関数の改善と、直交性・determinant・geodesic residualを分けて読む。",
                "Separate objective progress from orthogonality, determinant, "
                "and geodesic diagnostics.",
            ),
            misconception=_localized(
                "projection後にfeasibleなら、ambient updateとmanifold updateは同じ一歩である。",
                "A feasible projected point makes an ambient update equivalent "
                "to a manifold update.",
            ),
            expected_phenomenon_ja=(
                "どちらもSO(3)上に戻るが、projection correctionと接空間stepの意味は異なる。"
            ),
            expected_phenomenon_en=(
                "Both remain on SO(3), but projection correction and a tangent-space "
                "step have different meanings."
            ),
            success_signals=[
                VisualizationSignal(
                    signal_id="feasibility_and_progress_visible",
                    label_ja="構造残差と目的関数を同じevaluationで確認できる",
                    label_en="structure residuals and objective progress remain jointly visible",
                    observable_ids=[
                        "objective_value",
                        "geodesic_residual",
                        "orthogonality_error",
                        "determinant_error",
                    ],
                )
            ],
            failure_signals=(
                [
                    VisualizationSignal(
                        signal_id="projection_equivalence_misread",
                        label_ja="projection correctionを接空間stepと同一視してしまう",
                        label_en="projection correction is mistaken for a tangent-space step",
                        observable_ids=[
                            "objective_value",
                            "geodesic_residual",
                            "orthogonality_error",
                        ],
                    )
                ]
                if is_projected
                else []
            ),
            primary_observables=observables[:3],
            secondary_observables=observables[3:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="near-pi初期残差を確認",
                    title_en="Inspect the near-pi initial residual",
                    observable_ids=["objective_value", "geodesic_residual"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="最初のfeasibility mapを読む",
                    title_en="Read the first feasibility map",
                    observable_ids=["orthogonality_error", "determinant_error"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="objectiveとgeodesic residualを分離",
                    title_en="Separate objective and geodesic residual",
                    observable_ids=["objective_value", "geodesic_residual"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="feasible iterateと収束claimを分離",
                    title_en="Separate feasible iterates from convergence claims",
                    observable_ids=[
                        "objective_value",
                        "orthogonality_error",
                        "determinant_error",
                    ],
                ),
            ],
            comparison_role="sensitivity_variant" if is_projected else "primary_example",
            prerequisite_concept_ids=[
                "concept.manifold",
                "concept.so3-rotation-representation",
            ],
            recommended_next_scenario_ids=[counterpart],
            known_reference_display=KnownReferenceDisplay(
                policy="show",
                note_ja=(
                    "固定target rotationは目的値0の教材referenceであり、一般性能rankingではない。"
                ),
                note_en=(
                    "The fixed target rotation is a zero-loss teaching reference, "
                    "not a general ranking."
                ),
            ),
            static_summary=_localized(
                "同じnear-pi targetへ向かう12 updateで、lossとSO(3)構造残差を追う。",
                "Follow loss and SO(3) structure residuals over twelve updates "
                "to one near-pi target.",
            ),
            text_alternative=_localized(
                "identityから開始し、12 updateでgeodesic residualを縮めながら"
                "直交性とdeterminantを保つ。",
                "Starting at identity, twelve updates reduce geodesic residual "
                "while preserving orthogonality and determinant.",
            ),
            derived_media_caption=_localized(
                "SO(3) attitude alignmentのfeasibility診断",
                "Feasibility diagnostics for SO(3) attitude alignment",
            ),
            limitations_ja=(
                "固定3対応・noiseなし・固定stepの教材であり、rotation averagingのrobustness、"
                "near-pi chartの一般的安定性、実装速度、局所解の一般保証を示さない。"
            ),
            limitations_en=(
                "A noiseless fixed-three-correspondence lesson with a fixed step; it does not "
                "establish robust rotation averaging, general near-pi chart stability, runtime, "
                "or general local-solution guarantees."
            ),
        ),
        guided_story=None,
        experiment=VisualizationExperiment(
            oracle_policy=["objective_value", "gradient", "constraint_value"],
            initial_condition=VisualizationInitialCondition(point=initial_point),
            parameter_preset_id=str(trace.preset["preset_id"]),
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=EVALUATION_BUDGET),
            stopping={"max_oracle_evaluations": EVALUATION_BUDGET},
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id=f"RUN_{trace.trace_id.upper().replace('-', '_')}",
                method_id=trace.method_id,
                profile_id=trace.profile_id,
                implementation_mapping_status=trace.implementation_mapping_status,
                implementation_id=trace.implementation_id,
                artifact_id=trace.trace_id,
            )
        ],
        artifact=VisualizationArtifact(
            artifact_kind="executable_trace",
            artifact_contract="AlgorithmTrace",
            artifact_contract_version="1.0.0",
            renderer_family="generic_metric_history",
            renderer_contract_version="1.0.0",
            observable_ids=[observable.observable_id for observable in observables],
            payload_path=f"traces/{trace.trace_id}.json",
            payload_bytes=len(payload),
            payload_sha256=sha256(payload).hexdigest(),
        ),
        source_ids=trace.source_ids,
        last_verified="2026-07-19",
    )
