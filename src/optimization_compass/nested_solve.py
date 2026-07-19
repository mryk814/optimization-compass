from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256
from typing import Literal

from optimization_compass.trace_models import (
    AlgorithmTrace,
    TraceFrame,
    TraceMetric,
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
)

BILEVEL_EXACT_TRACE_ID = "bilevel-regression-exact-inner"
BILEVEL_RELAXED_TRACE_ID = "bilevel-regression-relaxed-complementarity"
BILEVEL_EXACT_SCENARIO_ID = "SCENARIO_BILEVEL_REGRESSION_EXACT"
BILEVEL_RELAXED_SCENARIO_ID = "SCENARIO_BILEVEL_REGRESSION_RELAXED"
BILEVEL_PROBLEM_DEFINITION_ID = "PROBLEM_BILEVEL_REGRESSION"
BILEVEL_PROBLEM_INSTANCE_ID = "INSTANCE_BILEVEL_REGRESSION_2COEF"
BILEVEL_BENCHMARK_CONTEXT_ID = "BENCH_BILEVEL_REGRESSION_EDUCATIONAL_6"
BILEVEL_GENERATOR_ID = "educational.bilevel_regression_ledger.v1"
BILEVEL_GENERATOR_VERSION = "1.0.0"
BILEVEL_PROFILE_ID = "PROFILE_BILEVEL_REGRESSION_LEDGER"
HYBRID_CHATTERING_TRACE_ID = "hybrid-mode-chattering-ledger"
HYBRID_CHATTERING_SCENARIO_ID = "SCENARIO_HYBRID_MODE_CHATTERING"
HYBRID_PROBLEM_DEFINITION_ID = "PROBLEM_HYBRID_MODE_DISCOVERY"
HYBRID_PROBLEM_INSTANCE_ID = "INSTANCE_HYBRID_CHATTERING_LEDGER"
HYBRID_GENERATOR_ID = "educational.hybrid_mode_ledger.v1"
HYBRID_GENERATOR_VERSION = "1.0.0"
HYBRID_PROFILE_ID = "PROFILE_HYBRID_MODE_LEDGER"

_BILEVEL_COMMON_PARAMETERS: dict[str, object] = {
    "outer_step_policy": "fixed_teaching_sequence",
    "inner_policy": "warm_started_slsqp",
    "inner_tolerance": 1e-8,
    "inner_max_iterations": 100,
    "derivative_route": "implicit_active_set",
}


def generate_bilevel_regression_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    exact_values = [
        (0.128, 0.940, 8e-9, 31, 7e-10, 6e-9),
        (0.096, 0.701, 7e-9, 28, 6e-10, 5e-9),
        (0.071, 0.542, 6e-9, 24, 5e-10, 4e-9),
        (0.059, 0.491, 5e-9, 21, 4e-10, 3e-9),
        (0.052, 0.458, 4e-9, 19, 3e-10, 2e-9),
        (0.049, 0.447, 3e-9, 17, 2e-10, 1e-9),
        (0.048, 0.444, 2e-9, 16, 1e-10, 8e-10),
    ]
    relaxed_values = [
        (0.128, 0.940, 8e-9, 31, 9e-3, 6e-9),
        (0.087, 0.684, 7e-9, 27, 8e-3, 5e-9),
        (0.058, 0.521, 6e-9, 23, 7e-3, 4e-9),
        (0.043, 0.469, 5e-9, 20, 6e-3, 3e-9),
        (0.038, 0.441, 4e-9, 18, 5e-3, 2e-9),
        (0.035, 0.431, 3e-9, 16, 4e-3, 1e-9),
        (0.034, 0.428, 2e-9, 15, 4e-3, 8e-10),
    ]
    return [
        _bilevel_trace(
            dataset_version=dataset_version,
            trace_id=BILEVEL_EXACT_TRACE_ID,
            scenario_id=BILEVEL_EXACT_SCENARIO_ID,
            treatment="exact_kkt_complementarity",
            relaxation_parameter=0.0,
            values=exact_values,
            terminal_status="converged",
        ),
        _bilevel_trace(
            dataset_version=dataset_version,
            trace_id=BILEVEL_RELAXED_TRACE_ID,
            scenario_id=BILEVEL_RELAXED_SCENARIO_ID,
            treatment="finite_relaxation",
            relaxation_parameter=1e-2,
            values=relaxed_values,
            terminal_status="stopped",
        ),
    ]


def generate_hybrid_chattering_trace(*, dataset_version: str) -> AlgorithmTrace:
    values = [
        (3.20, 0.0, 0.0, 1.00, 0.20),
        (2.91, 1.0, 1.0, 0.50, 0.13),
        (2.69, 0.0, 2.0, 0.25, 0.09),
        (2.52, 1.0, 3.0, 0.12, 0.06),
        (2.39, 0.0, 4.0, 0.06, 0.04),
        (2.29, 1.0, 5.0, 0.03, 0.028),
        (2.21, 0.0, 6.0, 0.015, 0.019),
        (2.15, 1.0, 7.0, 0.008, 0.013),
    ]
    frames = [
        TraceFrame(
            frame_index=index,
            iteration=index,
            oracle_evaluations=index,
            elapsed_steps=index,
            elapsed_time_ms=float(index * 80),
            event_type="initialize" if index == 0 else "mode_switch" if index < 7 else "stop",
            decision="not_applicable" if index in {0, 7} else "accepted",
            explanation_key=(
                "initial_mode"
                if index == 0
                else "relaxed_mode_switch"
                if index < 7
                else "chattering_stop"
            ),
            event_label_ja=(
                "初期mode"
                if index == 0
                else "relaxed indicatorがmodeを切替"
                if index < 7
                else "switch間隔が縮まり停止"
            ),
            event_label_en=(
                "Initial mode"
                if index == 0
                else "Relaxed indicator switches mode"
                if index < 7
                else "Stop as switch intervals shrink"
            ),
            keyframe=index in {0, 3, 7},
            points=[],
            vectors=[],
            metrics=[
                _metric("objective_value", "目的関数値", "objective value", objective),
                _metric("mode_sequence", "active mode", "active mode", mode),
                _metric("mode_switch_count", "mode切替数", "mode switch count", switches),
                _metric(
                    "switching_interval",
                    "切替間隔",
                    "switching interval",
                    interval,
                    "normalized time",
                ),
                _metric("dynamics_defect", "dynamics defect", "dynamics defect", defect),
            ],
            payload={
                "mode_policy": "relaxed_mode_discovery",
                "active_mode": int(mode),
                "minimum_dwell_time": 0.0,
                "contact_model": "not_applicable",
            },
        )
        for index, (objective, mode, switches, interval, defect) in enumerate(values)
    ]
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=HYBRID_CHATTERING_TRACE_ID,
        method_id="M_DIRECT_COLLOCATION",
        profile_id=HYBRID_PROFILE_ID,
        objective_id=HYBRID_PROBLEM_INSTANCE_ID,
        scenario_id=HYBRID_CHATTERING_SCENARIO_ID,
        generator_id=HYBRID_GENERATOR_ID,
        generator_version=HYBRID_GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"kind": "tracking_with_relaxed_mode_discovery"},
        preset={"preset_id": "VIEW_HYBRID_MODE_CHATTERING", "contact_model": "not_applicable"},
        parameters={
            "mode_policy": "relaxed_mode_discovery",
            "minimum_dwell_time": 0.0,
            "switch_penalty": 0.0,
        },
        initial_state={"point": [0.0, 0.0], "mode": 0},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=len(values) - 1,
        stopping={"max_oracle_evaluations": len(values) - 1, "minimum_switch_interval": 0.01},
        environment={"runtime": "deterministic_teaching_ledger", "version": "1.0.0"},
        fairness_statement=(
            "固定したmode indicator履歴でchatteringの読み方だけを示す。"
            "contact/friction solverやhybrid手法の一般性能を比較しない。"
        ),
        frames=frames,
        terminal_status="stopped",
        terminal_summary_ja=(
            "目的関数とdynamics defectは下がったが、mode切替間隔が縮み続けたため、"
            "可解なhybrid trajectoryとは扱わず停止した。"
        ),
        terminal_summary_en=(
            "The objective and dynamics defect decreased, but shrinking mode-switch intervals "
            "triggered a stop rather than a claim of a valid hybrid trajectory."
        ),
        source_ids=["S042", "S043", "S056", "S076"],
    )


def _bilevel_trace(
    *,
    dataset_version: str,
    trace_id: str,
    scenario_id: str,
    treatment: str,
    relaxation_parameter: float,
    values: Sequence[tuple[float, float, float, int, float, float]],
    terminal_status: Literal["converged", "stopped"],
) -> AlgorithmTrace:
    frames = [
        TraceFrame(
            frame_index=index,
            iteration=index,
            oracle_evaluations=index,
            elapsed_steps=index,
            elapsed_time_ms=float(index * 100),
            event_type="initialize" if index == 0 else "outer_update" if index < 6 else "stop",
            decision="not_applicable" if index in {0, 6} else "accepted",
            explanation_key=(
                "initial_inner_solve"
                if index == 0
                else "implicit_outer_update"
                if index < 6
                else "residual_check"
            ),
            event_label_ja=(
                "inner solveを検証"
                if index == 0
                else "implicit derivativeでouterを更新"
                if index < 6
                else "保証範囲を確認して停止"
            ),
            event_label_en=(
                "Validate the inner solve"
                if index == 0
                else "Update the outer variable with an implicit derivative"
                if index < 6
                else "Stop after checking the guarantee boundary"
            ),
            keyframe=index in {0, 3, 6},
            points=[],
            vectors=[],
            metrics=[
                _metric("outer_objective", "outer objective", "outer objective", outer),
                _metric("inner_objective", "inner objective", "inner objective", inner),
                _metric("inner_residual", "inner residual", "inner residual", residual),
                _metric("inner_iterations", "inner iteration数", "inner iterations", iterations),
                _metric(
                    "complementarity_residual",
                    "complementarity residual",
                    "complementarity residual",
                    complementarity,
                ),
                _metric(
                    "stationarity_residual",
                    "stationarity residual",
                    "stationarity residual",
                    stationarity,
                ),
                _metric(
                    "relaxation_parameter",
                    "relaxation parameter",
                    "relaxation parameter",
                    relaxation_parameter,
                ),
            ],
            payload={
                "outer_iteration": index,
                "inner_status": "tolerance_met",
                "inner_policy": _BILEVEL_COMMON_PARAMETERS["inner_policy"],
                "inner_tolerance": _BILEVEL_COMMON_PARAMETERS["inner_tolerance"],
                "derivative_route": _BILEVEL_COMMON_PARAMETERS["derivative_route"],
                "complementarity_treatment": treatment,
                "relaxation_parameter": relaxation_parameter,
            },
        )
        for index, (outer, inner, residual, iterations, complementarity, stationarity) in enumerate(
            values
        )
    ]
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id,
        method_id="M_SLSQP",
        profile_id=BILEVEL_PROFILE_ID,
        objective_id=BILEVEL_PROBLEM_INSTANCE_ID,
        scenario_id=scenario_id,
        generator_id=BILEVEL_GENERATOR_ID,
        generator_version=BILEVEL_GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={
            "kind": "validation_loss_after_inner_nonnegative_regression",
            "inner_constraint": "nonnegative_coefficients",
        },
        preset={"preset_id": "VIEW_BILEVEL_REGRESSION_HISTORY"},
        parameters={
            **_BILEVEL_COMMON_PARAMETERS,
            "complementarity_treatment": treatment,
            "relaxation_parameter": relaxation_parameter,
        },
        initial_state={"point": [0.8], "outer_lambda": 0.8},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=len(values) - 1,
        stopping={
            "max_oracle_evaluations": len(values) - 1,
            "inner_tolerance": 1e-8,
            "outer_step_tolerance": 1e-4,
        },
        environment={"runtime": "deterministic_teaching_ledger", "version": "1.0.0"},
        fairness_statement=(
            "固定data・outer budget・inner policy・tolerance・implicit derivative routeを共有し、"
            "complementarity treatmentだけを変えるcontrast-only教材である。"
        ),
        frames=frames,
        terminal_status=terminal_status,
        terminal_summary_ja=(
            "inner toleranceとstationarity residualは満たした。"
            + (
                "exact KKT complementarityの固定教材判定も満たした。"
                if relaxation_parameter == 0.0
                else "有限relaxationで残差が残るため、exact complementarityとは判定しない。"
            )
        ),
        terminal_summary_en=(
            "The inner tolerance and stationarity residual passed. "
            + (
                "The fixed teaching check for exact KKT complementarity also passed."
                if relaxation_parameter == 0.0
                else (
                    "A finite-relaxation residual remains, so exact complementarity is not claimed."
                )
            )
        ),
        source_ids=["S055", "S056", "S064"],
    )


def build_nested_solve_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    """Build nested/hybrid scenarios without adding profile branches to the shared exporter."""
    if trace.profile_id not in {BILEVEL_PROFILE_ID, HYBRID_PROFILE_ID}:
        raise ValueError(f"unsupported nested-solve profile: {trace.profile_id}")
    is_bilevel = trace.profile_id == BILEVEL_PROFILE_ID
    is_relaxed = trace.scenario_id == BILEVEL_RELAXED_SCENARIO_ID
    payload = canonical_trace_bytes(trace)
    point = trace.initial_state.get("point")
    preset_id = trace.preset.get("preset_id")
    seed_status = trace.seed.get("status")
    seed_value = trace.seed.get("value")
    if not isinstance(point, list) or not all(
        isinstance(value, int | float) and not isinstance(value, bool) for value in point
    ):
        raise ValueError(f"trace {trace.trace_id} has no numeric initial condition")
    if not isinstance(preset_id, str) or not preset_id.strip():
        raise ValueError(f"trace {trace.trace_id} has no parameter preset ID")
    if seed_status not in {"fixed", "not_applicable"}:
        raise ValueError(f"trace {trace.trace_id} has unsupported seed status")
    if seed_value is not None and (isinstance(seed_value, bool) or not isinstance(seed_value, int)):
        raise ValueError(f"trace {trace.trace_id} has an invalid seed value")
    stopping: dict[str, bool | int | float] = {}
    for key, value in trace.stopping.items():
        if not isinstance(value, bool | int | float):
            raise ValueError(f"trace {trace.trace_id} has non-numeric stopping metadata")
        stopping[key] = value

    observable_ids = (
        [
            "outer_objective",
            "inner_objective",
            "inner_residual",
            "inner_iterations",
            "complementarity_residual",
            "stationarity_residual",
            "relaxation_parameter",
        ]
        if is_bilevel
        else [
            "mode_sequence",
            "mode_switch_count",
            "switching_interval",
            "dynamics_defect",
            "objective_value",
        ]
    )
    title_ja, title_en = {
        BILEVEL_EXACT_SCENARIO_ID: (
            "Bilevel回帰 · exact inner診断",
            "Bilevel regression · exact inner diagnostics",
        ),
        BILEVEL_RELAXED_SCENARIO_ID: (
            "Bilevel回帰 · finite relaxationの残差",
            "Bilevel regression · finite-relaxation failure",
        ),
        HYBRID_CHATTERING_SCENARIO_ID: (
            "Hybrid mode discovery · chattering診断",
            "Hybrid mode discovery · chattering ledger",
        ),
    }[trace.scenario_id]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja=title_ja,
        title_en=title_en,
        purpose=("mechanism" if is_bilevel and not is_relaxed else "failure_contrast"),
        problem_definition_id=(
            BILEVEL_PROBLEM_DEFINITION_ID if is_bilevel else HYBRID_PROBLEM_DEFINITION_ID
        ),
        problem_instance_id=trace.objective_id,
        lesson=_bilevel_lesson(is_relaxed=is_relaxed) if is_bilevel else _hybrid_lesson(),
        guided_story=None,
        experiment=VisualizationExperiment(
            oracle_policy=(
                ["objective_value", "constraint_value", "constraint_jacobian"]
                if is_bilevel
                else ["objective_value", "constraint_value"]
            ),
            initial_condition=VisualizationInitialCondition(
                point=[float(value) for value in point]
            ),
            parameter_preset_id=preset_id,
            seed=VisualizationSeed(status=seed_status, value=seed_value),
            budget=VisualizationBudget(metric="oracle_evaluations", value=trace.evaluation_budget),
            stopping=stopping,
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
            artifact_contract_version=trace.contract_version,
            renderer_family="generic_metric_history",
            renderer_contract_version="1.0.0",
            observable_ids=observable_ids,
            payload_path=f"traces/{trace.trace_id}.json",
            payload_bytes=len(payload),
            payload_sha256=sha256(payload).hexdigest(),
        ),
        source_ids=trace.source_ids,
        last_verified="2026-07-19",
    )


def _bilevel_lesson(*, is_relaxed: bool) -> VisualizationLesson:
    return VisualizationLesson(
        learning_objective=_localized(
            "outer progress、inner solve、complementarityを別々の履歴として読む",
            "Read outer progress, the inner solve, and complementarity as separate histories",
        ),
        misconception=_localized(
            "outer objectiveが下がればinnerの解品質とexact complementarityも確認できた",
            "A lower outer objective establishes inner-solve quality and exact complementarity",
        ),
        expected_phenomenon_ja=(
            "有限relaxationではouter objectiveが下がってもcomplementarity residualが残る"
            if is_relaxed
            else "outer updateの前にinner toleranceとKKT residualを別々に確認する"
        ),
        expected_phenomenon_en=(
            "A finite relaxation can lower the outer objective while leaving a "
            "complementarity residual"
            if is_relaxed
            else "Check the inner tolerance and KKT residuals separately before each outer update"
        ),
        success_signals=[
            _signal(
                "nested_diagnostics_visible",
                "outer objective、inner residual、complementarity residualを"
                "同じouter evaluationで確認できる",
                "Outer objective, inner residual, and complementarity residual are "
                "visible at each outer evaluation",
                "outer_objective",
                "inner_residual",
                "complementarity_residual",
            )
        ],
        failure_signals=[
            _signal(
                "relaxation_is_not_exact",
                (
                    "有限relaxationでcomplementarity residualが残り、exactとは判定できない"
                    if is_relaxed
                    else (
                        "小さいstationarity residualだけではCQ、解写像の滑らかさ、"
                        "global最適性を確認できない"
                    )
                ),
                (
                    "A finite-relaxation residual remains, so exact complementarity "
                    "is not established"
                    if is_relaxed
                    else (
                        "A small stationarity residual does not establish a constraint "
                        "qualification, a smooth solution map, or global optimality"
                    )
                ),
                "stationarity_residual",
                "complementarity_residual",
            )
        ],
        primary_observables=[
            _observable("outer_objective", "outer objective", "outer objective"),
            _observable("inner_objective", "inner objective", "inner objective"),
            _observable("inner_residual", "inner residual", "inner residual"),
            _observable(
                "complementarity_residual",
                "complementarity residual",
                "complementarity residual",
            ),
        ],
        secondary_observables=[
            _observable("inner_iterations", "inner iteration数", "inner iterations"),
            _observable("stationarity_residual", "stationarity residual", "stationarity residual"),
            _observable("relaxation_parameter", "relaxation parameter", "relaxation parameter"),
        ],
        narration_steps=[
            _step(
                "start",
                "outerとinnerの目的関数を分けて確認",
                "Separate the outer and inner objectives",
                "outer_objective",
                "inner_objective",
            ),
            _step(
                "first_change",
                "inner toleranceを満たしてからouterを更新",
                "Update the outer variable only after the inner tolerance passes",
                "inner_residual",
                "inner_iterations",
            ),
            _step(
                "pattern_visible",
                "stationarityとcomplementarityを別々に確認",
                "Read stationarity and complementarity separately",
                "stationarity_residual",
                "complementarity_residual",
            ),
            _step(
                "termination",
                "relaxation・CQ・stationarityの保証範囲を限定",
                "Bound the claims from relaxation, constraint qualifications, and stationarity",
                "complementarity_residual",
                "relaxation_parameter",
            ),
        ],
        comparison_role="failure_contrast" if is_relaxed else "primary_example",
        prerequisite_concept_ids=[
            "F_STRUCTURE_BILEVEL",
            "F_DERIVATIVE_INNER_ITERATION",
            "F_STRUCTURE_COMPLEMENTARITY",
        ],
        recommended_next_scenario_ids=(
            [BILEVEL_EXACT_SCENARIO_ID]
            if is_relaxed
            else [BILEVEL_RELAXED_SCENARIO_ID, HYBRID_CHATTERING_SCENARIO_ID]
        ),
        known_reference_display=KnownReferenceDisplay(
            policy="not_shown",
            note_ja=(
                "固定ledgerはglobal bilevel optimum、MPEC stationarity class、CQ成立を表示しない。"
            ),
            note_en=(
                "The fixed ledger does not show a global bilevel optimum, an MPEC "
                "stationarity class, or a verified constraint qualification."
            ),
        ),
        static_summary=_localized(
            "outer objective、inner objective、inner residual、stationarity、"
            "complementarityをouter evaluationごとに並べる。",
            "Align outer and inner objectives, inner residual, stationarity, and "
            "complementarity by outer evaluation.",
        ),
        text_alternative=_localized(
            "各outer evaluationのinner iteration数、inner residual、stationarity residual、"
            "complementarity residual、relaxation parameterを列挙する。",
            "List inner iterations, inner residual, stationarity residual, "
            "complementarity residual, and the relaxation parameter at each outer "
            "evaluation.",
        ),
        derived_media_caption=_localized(
            "非負回帰のbilevel outer/inner診断ledger",
            "Bilevel outer/inner diagnostic ledger for nonnegative regression",
        ),
        limitations_ja=(
            "固定した2係数・6 outer updateの教育用ledgerであり、実solver executionではない。"
            "小さいresidualはglobal最適性、CQ、solution mapの滑らかさを保証せず、"
            "有限relaxationをexact complementarityとみなさない。"
        ),
        limitations_en=(
            "A fixed two-coefficient, six-outer-update teaching ledger rather than a "
            "solver execution. Small residuals do not establish global optimality, a "
            "constraint qualification, or a smooth solution map, and finite relaxation "
            "is not exact complementarity."
        ),
    )


def _hybrid_lesson() -> VisualizationLesson:
    return VisualizationLesson(
        learning_objective=_localized(
            "目的関数とdynamics defectが改善してもmode chatteringを独立して止める",
            "Stop mode chattering independently even when objective and dynamics defect improve",
        ),
        misconception=_localized(
            "連続状態と目的関数が滑らかならmode sequenceも妥当である",
            "A smooth state and objective imply a valid mode sequence",
        ),
        expected_phenomenon_ja="relaxed mode indicatorの切替間隔が縮み、mode switch数が増え続ける",
        expected_phenomenon_en=(
            "Switch intervals shrink and the switch count keeps increasing for a "
            "relaxed mode indicator"
        ),
        success_signals=[
            _signal(
                "mode_diagnostics_visible",
                "active mode、切替数、切替間隔を目的関数と分けて確認できる",
                "Active mode, switch count, and switch interval remain separate from the objective",
                "mode_sequence",
                "mode_switch_count",
                "switching_interval",
            )
        ],
        failure_signals=[
            _signal(
                "chattering_visible",
                "目的関数が下がっても切替間隔が縮み続ける",
                "Switch intervals continue shrinking even as the objective decreases",
                "objective_value",
                "mode_switch_count",
                "switching_interval",
            )
        ],
        primary_observables=[
            _observable("mode_sequence", "active mode", "active mode"),
            _observable("mode_switch_count", "mode切替数", "mode switch count"),
            _observable("switching_interval", "切替間隔", "switching interval"),
        ],
        secondary_observables=[
            _observable("dynamics_defect", "dynamics defect", "dynamics defect"),
            _observable("objective_value", "目的関数値", "objective value"),
        ],
        narration_steps=[
            _step(
                "start",
                "初期modeと目的関数を確認",
                "Inspect the initial mode and objective",
                "mode_sequence",
                "objective_value",
            ),
            _step(
                "first_change",
                "最初のmode switchを確認",
                "Inspect the first mode switch",
                "mode_sequence",
                "mode_switch_count",
            ),
            _step(
                "pattern_visible",
                "切替間隔が縮むpatternを確認",
                "Inspect the shrinking switch-interval pattern",
                "mode_switch_count",
                "switching_interval",
            ),
            _step(
                "termination",
                "目的改善とは別にchatteringで停止",
                "Stop for chattering independently of objective progress",
                "objective_value",
                "switching_interval",
            ),
        ],
        comparison_role="failure_contrast",
        prerequisite_concept_ids=[
            "F_CONSTRAINT_LOGICAL",
            "F_NUM_DISCRETE_VARIABLES",
            "F_STRUCTURE_TRAJECTORY",
        ],
        recommended_next_scenario_ids=[BILEVEL_EXACT_SCENARIO_ID],
        known_reference_display=KnownReferenceDisplay(
            policy="not_shown",
            note_ja="mode scheduleのglobal最適性やcontact/frictionの物理的妥当性は表示しない。",
            note_en=(
                "The display does not establish global optimality of the mode schedule "
                "or physical validity of contact or friction."
            ),
        ),
        static_summary=_localized(
            "mode indicator、切替数、切替間隔、dynamics defect、目的関数を同じevaluationで並べる。",
            "Align the mode indicator, switch count, switch interval, dynamics defect, "
            "and objective by evaluation.",
        ),
        text_alternative=_localized(
            "各evaluationのactive modeと累積切替数を列挙し、切替間隔が短くなる一方で"
            "目的関数とdynamics defectが下がる固定failure ledgerを示す。",
            "List the active mode and cumulative switches at each evaluation in a fixed "
            "failure ledger where switch intervals shrink while objective and dynamics "
            "defect decrease.",
        ),
        derived_media_caption=_localized(
            "mode discovery relaxationのchattering診断ledger",
            "Chattering diagnostic ledger for a mode-discovery relaxation",
        ),
        limitations_ja=(
            "固定した合成mode sequenceの教育用ledgerであり、hybrid solver execution、"
            "contact/friction model、物理simulationではない。"
            "mode discoveryの一般性能やtrajectoryの可行性を保証しない。"
        ),
        limitations_en=(
            "A fixed synthetic mode-sequence teaching ledger, not a hybrid solver "
            "execution, contact/friction model, or physical simulation. It does not "
            "establish general mode-discovery performance or trajectory feasibility."
        ),
    )


def _localized(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def _observable(observable_id: str, ja: str, en: str) -> VisualizationObservable:
    return VisualizationObservable(observable_id=observable_id, label_ja=ja, label_en=en)


def _signal(signal_id: str, ja: str, en: str, *observable_ids: str) -> VisualizationSignal:
    return VisualizationSignal(
        signal_id=signal_id,
        label_ja=ja,
        label_en=en,
        observable_ids=list(observable_ids),
    )


def _step(
    milestone_id: Literal["start", "first_change", "pattern_visible", "termination"],
    ja: str,
    en: str,
    *observable_ids: str,
) -> VisualizationNarrationStep:
    return VisualizationNarrationStep(
        milestone_id=milestone_id,
        title_ja=ja,
        title_en=en,
        observable_ids=list(observable_ids),
    )


def _metric(
    metric_id: str,
    label_ja: str,
    label_en: str,
    value: float,
    unit: str | None = None,
) -> TraceMetric:
    return TraceMetric(
        metric_id=metric_id,
        label_ja=label_ja,
        label_en=label_en,
        value=float(value),
        unit=unit,
    )
