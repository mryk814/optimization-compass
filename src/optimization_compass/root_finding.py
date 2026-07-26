from __future__ import annotations

# ruff: noqa: E501
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

GENERATOR_ID = "educational.root_finding.v1"
GENERATOR_VERSION = "1.0.0"
PROFILE_ID = "PROFILE_ROOT_FINDING_EC028"
PROBLEM_DEFINITION_ID = "PROBLEM_ROOT_FINDING"
PROBLEM_INSTANCE_ID = "INSTANCE_ROOT_FINDING_EC028"
ROOT_SCENARIO_ID = "SCENARIO_ROOT_FINDING_COMPONENT_TOLERANCE"
SQUARED_SCENARIO_ID = "SCENARIO_ROOT_FINDING_SMALL_SQUARED_RESIDUAL"
ROOT_TRACE_ID = "root-finding-component-tolerance"
SQUARED_TRACE_ID = "root-finding-small-squared-residual"

Policy = Literal["root", "small_squared"]


def residuals(point: tuple[float, float]) -> tuple[float, float]:
    x1, x2 = point
    return (x1 * x1 + x2 - 1.0, x1 + x2 * x2 - 1.0)


def _metric(metric_id: str, ja: str, en: str, value: float, unit: str) -> TraceMetric:
    return TraceMetric(metric_id=metric_id, label_ja=ja, label_en=en, value=value, unit=unit)


def _frame(index: int, point: tuple[float, float], *, accepted: bool, policy: Policy) -> TraceFrame:
    r1, r2 = residuals(point)
    squared = 0.5 * (r1 * r1 + r2 * r2)
    maximum = max(abs(r1), abs(r2))
    return TraceFrame(
        frame_index=index,
        iteration=index,
        oracle_evaluations=index + 1,
        elapsed_steps=index,
        elapsed_time_ms=float((index + 1) * 10),
        event_type="initialize" if index == 0 else "update" if accepted else "stop",
        decision="not_applicable" if index == 0 else "accepted" if accepted else "rejected",
        explanation_key="root_finding.component_tolerance",
        event_label_ja=(
            "初期残差を記録"
            if index == 0
            else "根の成分別許容値を満たす"
            if accepted
            else "二乗和は小さいが成分別許容値を満たさない"
        ),
        event_label_en=(
            "Record initial residuals"
            if index == 0
            else "Meet component-wise root tolerance"
            if accepted
            else "Squared residual is small but component tolerance fails"
        ),
        keyframe=True,
        points=[],
        vectors=[],
        metrics=[
            _metric("residual_1", "残差 F1", "residual F1", r1, "residual"),
            _metric("residual_2", "残差 F2", "residual F2", r2, "residual"),
            _metric(
                "residual_max_abs", "最大絶対残差", "maximum absolute residual", maximum, "residual"
            ),
            _metric(
                "squared_residual", "二乗残差の半分", "half squared residual", squared, "objective"
            ),
        ],
        payload={
            "point": {"x1": point[0], "x2": point[1]},
            "residual_vector": [r1, r2],
            "component_tolerance": 0.02,
            "scalar_loss_threshold": 0.003,
            "stopping_policy": policy,
            "scope": "deterministic teaching ledger; not a SciPy root or least_squares benchmark",
        },
    )


def generate_root_finding_trace(*, dataset_version: str, policy: Policy) -> AlgorithmTrace:
    rows = [(0.7, 0.7), (0.618034, 0.618034)]
    if policy == "small_squared":
        rows = [(0.7, 0.7), (0.64, 0.64)]
    frames = [
        _frame(index, point, accepted=policy == "root" or index < len(rows) - 1, policy=policy)
        for index, point in enumerate(rows)
    ]
    small_squared = policy == "small_squared"
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=SQUARED_TRACE_ID if small_squared else ROOT_TRACE_ID,
        method_id="M_GAUSS_NEWTON",
        profile_id=PROFILE_ID,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=SQUARED_SCENARIO_ID if small_squared else ROOT_SCENARIO_ID,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"kind": "root_residual_vector", "equations": "[x1^2+x2-1, x1+x2^2-1]"},
        preset={"preset_id": "ROOT_FINDING_EC028_FIXED"},
        parameters={
            "component_tolerance": 0.02,
            "scalar_loss_threshold": 0.003,
            "changed_factor": "stopping_policy",
        },
        initial_state={"point": [0.7, 0.7], "decision_domain": "two_continuous_variables"},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=len(frames),
        stopping={
            "component_tolerance": 0.02,
            "scalar_loss_threshold": 0.003,
            "componentwise_required": policy == "root",
        },
        environment={
            "runtime": "deterministic_educational_root_ledger",
            "version": GENERATOR_VERSION,
        },
        fairness_statement="Both members use the same equations, domain, initial point, Jacobian availability, and residual scaling; only the stopping rule changes.",
        frames=frames,
        terminal_status="converged" if policy == "root" else "stopped",
        terminal_summary_ja=(
            "各残差の絶対値が0.02未満になったため、rootとして停止した。"
            if policy == "root"
            else "二乗残差は0.003未満だが、F1=0.0496が成分別許容値0.02を超えるためrootとは呼ばない。"
        ),
        terminal_summary_en=(
            "Both residual components are below 0.02, so the ledger stops as a root."
            if policy == "root"
            else "The squared residual is below 0.003, but F1=0.0496 exceeds the 0.02 component tolerance, so this is not called a root."
        ),
        source_ids=["S002", "S003", "S041", "S056", "S080"],
    )


def generate_root_finding_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    return [
        generate_root_finding_trace(dataset_version=dataset_version, policy="root"),
        generate_root_finding_trace(dataset_version=dataset_version, policy="small_squared"),
    ]


def _text(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def build_root_finding_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    small_squared = trace.scenario_id == SQUARED_SCENARIO_ID
    counterpart = ROOT_SCENARIO_ID if small_squared else SQUARED_SCENARIO_ID
    observables = [
        VisualizationObservable(
            observable_id="residual_1", label_ja="残差 F1", label_en="residual F1"
        ),
        VisualizationObservable(
            observable_id="residual_2", label_ja="残差 F2", label_en="residual F2"
        ),
        VisualizationObservable(
            observable_id="residual_max_abs",
            label_ja="最大絶対残差",
            label_en="maximum absolute residual",
        ),
        VisualizationObservable(
            observable_id="squared_residual",
            label_ja="二乗残差の半分",
            label_en="half squared residual",
        ),
    ]
    payload = canonical_trace_bytes(trace)
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja="求根: 二乗残差だけでは止めない"
        if small_squared
        else "求根: 各残差をゼロへ近づける",
        title_en="Root finding: do not stop on squared residual alone"
        if small_squared
        else "Root finding: drive each residual to zero",
        purpose="failure_contrast" if small_squared else "mechanism",
        problem_definition_id=PROBLEM_DEFINITION_ID,
        problem_instance_id=PROBLEM_INSTANCE_ID,
        lesson=VisualizationLesson(
            learning_objective=_text(
                "残差vector、最大絶対残差、二乗残差を別々に読む。",
                "Read the residual vector, maximum residual, and squared residual separately.",
            ),
            misconception=_text(
                "二乗残差が小さければ、各方程式を要求精度で満たしたrootである。",
                "A small squared residual means every equation meets the required root tolerance.",
            )
            if small_squared
            else None,
            expected_phenomenon_ja="同じ方程式と初期値でも、scalar lossだけの停止は一つの残差が大きい点をrootと誤読させる。",
            expected_phenomenon_en="With the same equations and start, scalar-loss stopping can misread a point with one large residual as a root.",
            success_signals=[
                VisualizationSignal(
                    signal_id="componentwise_reading",
                    label_ja="成分別に確認",
                    label_en="check components separately",
                    observable_ids=["residual_1", "residual_2", "residual_max_abs"],
                )
            ],
            failure_signals=[
                VisualizationSignal(
                    signal_id="scalar_only_stop",
                    label_ja="scalar lossだけで停止",
                    label_en="stop on scalar loss only",
                    observable_ids=["squared_residual", "residual_max_abs"],
                )
            ]
            if small_squared
            else [],
            primary_observables=observables[:3],
            secondary_observables=observables[3:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="残差vectorを置く",
                    title_en="Place the residual vector",
                    observable_ids=["residual_1", "residual_2"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="最大成分を読む",
                    title_en="Read the largest component",
                    observable_ids=["residual_max_abs"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="残差の偏りを読む",
                    title_en="Read the residual imbalance",
                    observable_ids=["residual_1", "residual_2", "residual_max_abs"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="停止理由を照合",
                    title_en="Check the stopping reason",
                    observable_ids=["residual_max_abs", "squared_residual"],
                ),
            ],
            comparison_role="failure_contrast" if small_squared else "primary_example",
            prerequisite_concept_ids=["concept.least-squares"],
            recommended_next_scenario_ids=[counterpart],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="大域的な根の列挙は表示しない。",
                note_en="No enumeration of global roots is shown.",
            ),
            static_summary=_text(
                "同じ連立方程式を、成分別許容値と二乗残差で読み比べる。",
                "Compare component tolerance and squared residual on the same equation system.",
            ),
            text_alternative=_text(
                "各反復のF1、F2、最大絶対残差、二乗残差、停止理由を列挙する。",
                "List F1, F2, maximum residual, squared residual, and stopping reason for every iteration.",
            ),
            derived_media_caption=_text(
                "連立方程式のroot-finding residual ledger", "Residual ledger for root finding"
            ),
            limitations_ja="決定的な2変数教材であり、SciPy、Gauss-Newton、Jacobian品質、複数根、大域収束、実計測のscale設定を比較しない。",
            limitations_en="A deterministic two-variable lesson; it does not compare SciPy, Gauss-Newton, Jacobian quality, multiple roots, global convergence, or real measurement scaling.",
        ),
        experiment=VisualizationExperiment(
            oracle_policy=["residual_vector", "jacobian"],
            initial_condition=VisualizationInitialCondition(point=[0.7, 0.7]),
            parameter_preset_id="ROOT_FINDING_EC028_FIXED",
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=trace.evaluation_budget),
            stopping={"oracle_evaluations": trace.evaluation_budget},
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id=f"RUN_{trace.trace_id.upper().replace('-', '_')}",
                method_id=trace.method_id,
                profile_id=trace.profile_id,
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=trace.trace_id,
            )
        ],
        artifact=VisualizationArtifact(
            artifact_kind="executable_trace",
            artifact_contract="AlgorithmTrace",
            artifact_contract_version="1.0.0",
            renderer_family="generic_metric_history",
            renderer_contract_version="1.0.0",
            observable_ids=[item.observable_id for item in observables],
            payload_path=f"traces/{trace.trace_id}.json",
            payload_bytes=len(payload),
            payload_sha256=sha256(payload).hexdigest(),
        ),
        source_ids=trace.source_ids,
        last_verified="2026-07-24",
    )
