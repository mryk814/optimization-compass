from __future__ import annotations

from hashlib import sha256
from typing import Literal

from optimization_compass.problem_registry import get_runtime_problem
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
    scenario_identity,
)

PROBLEM_DEFINITION_ID = "PROBLEM_SHAPE_OPTIMIZATION"
PROBLEM_INSTANCE_ID = "INSTANCE_DIFFUSER_SHAPE_3P"
PROFILE_ID = "PROFILE_SHAPE_DIFFUSER_GENERIC"
TOPOLOGY_PROFILE_ID = "PROFILE_TOPOLOGY_REPRESENTATION_GENERIC"

PRIMARY_SCENARIO_ID = "SCENARIO_SHAPE_DIFFUSER_VALID_UPDATE"
FAILURE_SCENARIO_ID = "SCENARIO_SHAPE_DIFFUSER_INVALID_GEOMETRY"
TOPOLOGY_CONTRAST_SCENARIO_ID = "SCENARIO_SHAPE_TOPOLOGY_REPRESENTATION_CONTRAST"

GENERATOR_ID = "educational.shape_optimization.v1"
GENERATOR_VERSION = "1.0.0"
SOURCE_IDS = ["S097", "S101", "S104", "S105", "S106"]

FrameValue = tuple[float, float, float, float, float, float, float]


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
    metric_id: str, label_ja: str, label_en: str, value: float, unit: str | None = None
) -> TraceMetric:
    return TraceMetric(
        metric_id=metric_id,
        label_ja=label_ja,
        label_en=label_en,
        value=value,
        unit=unit,
    )


def _shape_trace(
    *,
    dataset_version: str,
    trace_id: str,
    scenario_id: str,
    method_id: str,
    profile_id: str,
    representation: str,
    topology_change_allowed: bool,
    values: list[FrameValue],
    terminal_status: Literal["completed", "failed"],
    terminal_summary_ja: str,
    terminal_summary_en: str,
) -> AlgorithmTrace:
    frames: list[TraceFrame] = []
    for index, value in enumerate(values):
        (
            parameter_update_norm,
            geometry_min_gap,
            mesh_min_quality,
            inverted_cells,
            state_residual,
            objective_value,
            representation_freedom,
        ) = value
        terminal_failure = terminal_status == "failed" and index == len(values) - 1
        terminal = index == len(values) - 1
        frames.append(
            TraceFrame(
                frame_index=index,
                iteration=index,
                oracle_evaluations=index,
                elapsed_steps=index,
                elapsed_time_ms=float(index * 80),
                event_type=(
                    "initialize"
                    if index == 0
                    else "geometry-failure"
                    if terminal_failure
                    else "stop"
                    if terminal
                    else "update"
                ),
                decision="not_applicable" if index == 0 or terminal else "accepted",
                explanation_key=(
                    "initial-shape"
                    if index == 0
                    else "invalid-geometry"
                    if terminal_failure
                    else "shape-update"
                ),
                event_label_ja=(
                    "初期shape"
                    if index == 0
                    else "geometryが無効"
                    if terminal_failure
                    else "shapeを更新"
                ),
                event_label_en=(
                    "Initial shape"
                    if index == 0
                    else "Invalid geometry"
                    if terminal_failure
                    else "Update shape"
                ),
                keyframe=index in {0, round((len(values) - 1) / 2), len(values) - 1},
                points=[],
                vectors=[],
                metrics=[
                    _metric(
                        "parameter_update_norm",
                        "parameter update norm",
                        "parameter update norm",
                        parameter_update_norm,
                    ),
                    _metric(
                        "geometry_min_gap",
                        "geometry最小gap",
                        "minimum geometry gap",
                        geometry_min_gap,
                    ),
                    _metric(
                        "mesh_min_quality",
                        "mesh最小quality",
                        "minimum mesh quality",
                        mesh_min_quality,
                    ),
                    _metric(
                        "inverted_cells", "反転cell数", "inverted cells", inverted_cells, "cells"
                    ),
                    _metric("state_residual", "state residual", "state residual", state_residual),
                    _metric("objective_value", "目的関数値", "objective value", objective_value),
                    _metric(
                        "representation_freedom",
                        "表現自由度",
                        "representation freedom",
                        representation_freedom,
                    ),
                ],
                payload={
                    "parameter": {
                        "update_norm": parameter_update_norm,
                        "representation": representation,
                    },
                    "geometry": {
                        "minimum_gap": geometry_min_gap,
                        "self_intersection": geometry_min_gap <= 0.0,
                        "topology_change_allowed": topology_change_allowed,
                    },
                    "mesh": {
                        "minimum_quality": mesh_min_quality,
                        "inverted_cells": int(inverted_cells),
                    },
                    "physical_state": {"residual": state_residual},
                    "objective_value": objective_value,
                },
            )
        )
    runtime = get_runtime_problem(PROBLEM_INSTANCE_ID)
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id,
        method_id=method_id,
        profile_id=profile_id,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=scenario_id,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective=runtime.trace_objective(),
        preset={"preset_id": "PRESET_SHAPE_DIFFUSER_3P"},
        parameters={
            "representation": representation,
            "topology_change_allowed": topology_change_allowed,
            "geometry_samples": 21,
        },
        initial_state={"point": [1.15, 0.0, 0.0]},
        seed={"status": "fixed", "value": 134},
        evaluation_budget=6,
        stopping={
            "max_oracle_evaluations": 6,
            "geometry_min_gap": 0.4,
            "mesh_min_quality": 0.2,
            "state_residual_tolerance": 0.000001,
        },
        environment={
            "runtime": "deterministic_educational_generator",
            "version": GENERATOR_VERSION,
        },
        fairness_statement=(
            "同じ物理brief、初期外形、設計envelope、診断、予算、tolerance、seedを固定した"
            "表現contrastであり、手法性能を順位付けしない。"
        ),
        frames=frames,
        terminal_status=terminal_status,
        terminal_summary_ja=terminal_summary_ja,
        terminal_summary_en=terminal_summary_en,
        source_ids=SOURCE_IDS,
    )


def generate_shape_optimization_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    primary_values: list[FrameValue] = [
        (0.00, 2.00, 0.92, 0.0, 0.0000004, 0.100, 3.0),
        (0.08, 1.86, 0.89, 0.0, 0.0000005, 0.076, 3.0),
        (0.07, 1.72, 0.85, 0.0, 0.0000005, 0.055, 3.0),
        (0.06, 1.61, 0.81, 0.0, 0.0000006, 0.037, 3.0),
        (0.05, 1.52, 0.77, 0.0, 0.0000006, 0.024, 3.0),
        (0.04, 1.45, 0.73, 0.0, 0.0000007, 0.015, 3.0),
        (0.03, 1.40, 0.70, 0.0, 0.0000007, 0.011, 3.0),
    ]
    failure_values: list[FrameValue] = [
        (0.00, 2.00, 0.92, 0.0, 0.0000004, 0.100, 3.0),
        (0.20, 1.35, 0.72, 0.0, 0.0000008, 0.061, 3.0),
        (0.28, 0.82, 0.48, 0.0, 0.0000030, 0.032, 3.0),
        (0.34, 0.41, 0.24, 0.0, 0.0000200, 0.018, 3.0),
        (0.40, 0.16, 0.08, 2.0, 0.0004000, 0.012, 3.0),
        (0.45, 0.03, 0.01, 5.0, 0.0030000, 0.009, 3.0),
        (0.50, -0.08, -0.05, 9.0, 0.0080000, 0.007, 3.0),
    ]
    topology_values: list[FrameValue] = [
        (0.00, 2.00, 0.92, 0.0, 0.0000004, 0.100, 32.0),
        (0.08, 1.88, 0.90, 0.0, 0.0000005, 0.082, 32.0),
        (0.07, 1.77, 0.87, 0.0, 0.0000005, 0.066, 32.0),
        (0.06, 1.66, 0.84, 0.0, 0.0000006, 0.052, 32.0),
        (0.05, 1.58, 0.82, 0.0, 0.0000006, 0.041, 32.0),
        (0.04, 1.51, 0.79, 0.0, 0.0000007, 0.033, 32.0),
        (0.03, 1.46, 0.77, 0.0, 0.0000007, 0.028, 32.0),
    ]
    return [
        _shape_trace(
            dataset_version=dataset_version,
            trace_id="shape-diffuser-valid-update",
            scenario_id=PRIMARY_SCENARIO_ID,
            method_id="M_SLSQP",
            profile_id=PROFILE_ID,
            representation="three_parameter_fixed_topology",
            topology_change_allowed=False,
            values=primary_values,
            terminal_status="completed",
            terminal_summary_ja="目的値と同時にgeometry、mesh、stateの診断が有効範囲に残る更新を完了しました。",
            terminal_summary_en=(
                "The update completes with geometry, mesh, and state diagnostics still valid."
            ),
        ),
        _shape_trace(
            dataset_version=dataset_version,
            trace_id="shape-diffuser-invalid-geometry",
            scenario_id=FAILURE_SCENARIO_ID,
            method_id="M_SLSQP",
            profile_id=PROFILE_ID,
            representation="three_parameter_fixed_topology",
            topology_change_allowed=False,
            values=failure_values,
            terminal_status="failed",
            terminal_summary_ja="目的proxyは下がりましたが、自己交差と反転cellが生じたため候補を無効とします。",
            terminal_summary_en=(
                "The objective proxy decreases, but self-intersection and inverted cells "
                "make the candidate invalid."
            ),
        ),
        _shape_trace(
            dataset_version=dataset_version,
            trace_id="shape-topology-representation-contrast",
            scenario_id=TOPOLOGY_CONTRAST_SCENARIO_ID,
            method_id="M_SIMP_TOPOLOGY",
            profile_id=TOPOLOGY_PROFILE_ID,
            representation="density_field_topology_change",
            topology_change_allowed=True,
            values=topology_values,
            terminal_status="completed",
            terminal_summary_ja=(
                "同じ物理briefでもdensity fieldは接続を変えられます。"
                "objective値の順位には使いません。"
            ),
            terminal_summary_en=(
                "A density field can change connectivity under the same physical brief; "
                "the values are not used for ranking."
            ),
        ),
    ]


def _lesson(trace: AlgorithmTrace) -> VisualizationLesson:
    is_failure = trace.scenario_id == FAILURE_SCENARIO_ID
    is_topology_contrast = trace.scenario_id == TOPOLOGY_CONTRAST_SCENARIO_ID
    role: Literal["primary_example", "failure_contrast", "baseline"] = (
        "failure_contrast"
        if is_failure
        else "baseline"
        if is_topology_contrast
        else "primary_example"
    )
    next_scenarios = (
        [PRIMARY_SCENARIO_ID]
        if is_failure or is_topology_contrast
        else [FAILURE_SCENARIO_ID, TOPOLOGY_CONTRAST_SCENARIO_ID]
    )
    expected_ja = (
        "目的proxyが下がってもgeometry最小gapとmesh qualityが閾値を破れば候補は無効になる"
        if is_failure
        else (
            "density fieldは接続変更を許すため、"
            "fixed-topology shape parameterと同じ設計空間ではない"
        )
        if is_topology_contrast
        else "parameter更新後もgeometry、mesh、state、目的を別々に確認して候補を受理する"
    )
    expected_en = (
        "A lower objective proxy does not rescue a candidate that violates geometry-gap "
        "and mesh-quality checks"
        if is_failure
        else (
            "A density field can change connectivity and therefore does not share the "
            "same design space as fixed-topology shape parameters"
        )
        if is_topology_contrast
        else (
            "Accept an update only after parameter, geometry, mesh, state, and objective "
            "checks remain distinct"
        )
    )
    return VisualizationLesson(
        learning_objective=_localized(
            "parameter、geometry、mesh、physical state、目的を同じevaluation軸で分けて読む",
            "Separate parameters, geometry, mesh, physical state, and objective on one "
            "evaluation axis",
        ),
        misconception=_localized(
            "離散目的が改善すればgeometryとmeshも有効で、連続体性能も改善している",
            "An improved discrete objective implies valid geometry, a valid mesh, and "
            "improved continuous-domain performance",
        ),
        expected_phenomenon_ja=expected_ja,
        expected_phenomenon_en=expected_en,
        success_signals=[
            _signal(
                "layered_shape_diagnostics_visible",
                "parameter更新とgeometry、mesh、stateの診断を別々に確認できる",
                "Parameter updates and geometry, mesh, and state diagnostics remain "
                "separately visible",
                "parameter_update_norm",
                "geometry_min_gap",
                "mesh_min_quality",
                "state_residual",
            )
        ],
        failure_signals=[
            _signal(
                "invalid_geometry_or_mesh",
                "自己交差、gap消失、反転cellを目的改善より先に検出する",
                "Detect self-intersection, gap closure, and inverted cells before reading "
                "objective improvement",
                "geometry_min_gap",
                "mesh_min_quality",
                "inverted_cells",
            )
        ],
        primary_observables=[
            _observable("geometry_min_gap", "geometry最小gap", "minimum geometry gap"),
            _observable("mesh_min_quality", "mesh最小quality", "minimum mesh quality"),
            _observable("state_residual", "state residual", "state residual"),
        ],
        secondary_observables=[
            _observable("parameter_update_norm", "parameter update norm", "parameter update norm"),
            _observable("inverted_cells", "反転cell数", "inverted cells"),
            _observable("objective_value", "目的関数値", "objective value"),
            _observable("representation_freedom", "表現自由度", "representation freedom"),
        ],
        narration_steps=[
            _step(
                "start",
                "初期parameterとgeometryを確認",
                "Inspect the initial parameters and geometry",
                "parameter_update_norm",
                "geometry_min_gap",
            ),
            _step(
                "first_change",
                "最初のgeometry／mesh変化を追う",
                "Follow the first geometry and mesh change",
                "geometry_min_gap",
                "mesh_min_quality",
            ),
            _step(
                "pattern_visible",
                "目的とvalidity診断を分ける",
                "Separate objective progress from validity diagnostics",
                "objective_value",
                "geometry_min_gap",
                "inverted_cells",
            ),
            _step(
                "termination",
                "受理、failure、表現差を判定",
                "Classify acceptance, failure, or representation difference",
                "mesh_min_quality",
                "state_residual",
                "representation_freedom",
            ),
        ],
        comparison_role=role,
        prerequisite_concept_ids=["F_STRUCTURE_PDE_CONSTRAINED", "F_VARIABLE_DOMAIN"],
        recommended_next_scenario_ids=next_scenarios,
        known_reference_display=KnownReferenceDisplay(
            policy="not_shown",
            note_ja=(
                "低cost proxyの既知parameter解を連続PDEや別parameterizationの最適解として表示しない"
            ),
            note_en=(
                "Do not display a reduced-proxy parameter solution as the optimum of a "
                "continuous PDE or another parameterization"
            ),
        ),
        static_summary=_localized(
            "diffuser更新ごとにparameter、geometry gap、mesh quality、"
            "state residual、目的を並べる。",
            "Align parameters, geometry gap, mesh quality, state residual, and objective "
            "for each diffuser update.",
        ),
        text_alternative=_localized(
            "各evaluationのupdate norm、gap、quality、反転cell、state residual、"
            "目的、表現自由度を列挙する。",
            "List update norm, gap, quality, inverted cells, state residual, objective, "
            "and representation freedom at every evaluation.",
        ),
        derived_media_caption=_localized(
            "2D diffuser shapeのgeometry・mesh・state診断履歴",
            "Geometry, mesh, and state diagnostics for a 2D diffuser shape",
        ),
        limitations_ja=(
            "3 parameterと低cost state proxyの決定論的教材であり、CFD、連続体可行性、"
            "mesh independence、実性能、shape／topologyの一般rankingを保証しない"
        ),
        limitations_en=(
            "A deterministic three-parameter lesson with a low-cost state proxy; it does "
            "not establish CFD, continuous-domain feasibility, mesh independence, real "
            "performance, or a general shape-versus-topology ranking"
        ),
    )


def build_shape_optimization_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    if trace.profile_id not in {PROFILE_ID, TOPOLOGY_PROFILE_ID}:
        raise ValueError(f"unsupported shape-optimization profile: {trace.profile_id}")
    point = trace.initial_state.get("point")
    preset_id = trace.preset.get("preset_id")
    seed_value = trace.seed.get("value")
    if not isinstance(point, list) or not all(isinstance(value, int | float) for value in point):
        raise ValueError(f"trace {trace.trace_id} has no numeric initial condition")
    if not isinstance(preset_id, str) or not preset_id.strip():
        raise ValueError(f"trace {trace.trace_id} has no parameter preset ID")
    if isinstance(seed_value, bool) or not isinstance(seed_value, int):
        raise ValueError(f"trace {trace.trace_id} has no fixed seed")
    purpose: Literal["mechanism", "comparison", "failure_contrast"] = (
        "failure_contrast"
        if trace.scenario_id == FAILURE_SCENARIO_ID
        else "comparison"
        if trace.scenario_id == TOPOLOGY_CONTRAST_SCENARIO_ID
        else "mechanism"
    )
    titles = {
        PRIMARY_SCENARIO_ID: ("2D diffuser · 有効なshape更新", "2D diffuser · valid shape update"),
        FAILURE_SCENARIO_ID: (
            "2D diffuser · geometry／mesh failure",
            "2D diffuser · geometry and mesh failure",
        ),
        TOPOLOGY_CONTRAST_SCENARIO_ID: (
            "shape／topology表現contrast",
            "Shape/topology representation contrast",
        ),
    }
    identity_status, canonical_scenario_id = scenario_identity(trace.scenario_id)
    payload = canonical_trace_bytes(trace)
    observable_ids = [
        "parameter_update_norm",
        "geometry_min_gap",
        "mesh_min_quality",
        "inverted_cells",
        "state_residual",
        "objective_value",
        "representation_freedom",
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status=identity_status,
        canonical_scenario_id=canonical_scenario_id,
        title_ja=titles[trace.scenario_id][0],
        title_en=titles[trace.scenario_id][1],
        purpose=purpose,
        problem_definition_id=PROBLEM_DEFINITION_ID,
        problem_instance_id=PROBLEM_INSTANCE_ID,
        lesson=_lesson(trace),
        experiment=VisualizationExperiment(
            oracle_policy=[
                "objective_value",
                "gradient",
                "constraint_value",
                "constraint_jacobian",
            ],
            initial_condition=VisualizationInitialCondition(
                point=[float(value) for value in point]
            ),
            parameter_preset_id=preset_id,
            seed=VisualizationSeed(status="fixed", value=seed_value),
            budget=VisualizationBudget(metric="oracle_evaluations", value=trace.evaluation_budget),
            stopping={
                key: value
                for key, value in trace.stopping.items()
                if isinstance(value, bool | int | float)
            },
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
