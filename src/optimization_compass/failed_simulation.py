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

GENERATOR_ID = "educational.failed_simulation.v1"
GENERATOR_VERSION = "1.0.0"
PROFILE_ID = "PROFILE_FAILED_SIMULATION_EC027"
PROBLEM_DEFINITION_ID = "PROBLEM_FAILED_SIMULATION"
PROBLEM_INSTANCE_ID = "INSTANCE_FAILED_SIMULATION_EC027"
FEASIBLE_SCENARIO_ID = "SCENARIO_FAILED_SIMULATION_FEASIBLE_LEDGER"
FAILURE_SCENARIO_ID = "SCENARIO_FAILED_SIMULATION_FAILURE_LEDGER"
FEASIBLE_TRACE_ID = "failed-simulation-feasible-ledger"
FAILURE_TRACE_ID = "failed-simulation-failure-ledger"

Policy = Literal["feasible", "failure"]


def _metric(metric_id: str, ja: str, en: str, value: float, unit: str) -> TraceMetric:
    return TraceMetric(metric_id=metric_id, label_ja=ja, label_en=en, value=value, unit=unit)


def _frame(
    *, index: int, u1: float, u2: float, mode: int, status: str, value: float | None
) -> TraceFrame:
    feasible = status == "ok"
    prior_successes = [0, 1, 2, 2, 3, 4, 5][index]
    successes = prior_successes + int(feasible)
    evaluations = index + 1
    best_feasible = min(0.1225, 0.0425, 0.0225, 0.0125, 0.0025) if successes >= 5 else 0.0
    return TraceFrame(
        frame_index=index,
        iteration=index,
        oracle_evaluations=evaluations,
        elapsed_steps=index,
        elapsed_time_ms=float(evaluations * 1000),
        event_type="simulation_success" if feasible else "simulation_failed",
        decision="accepted" if feasible else "rejected",
        explanation_key=f"failed_simulation.{status}",
        event_label_ja="成功したsimulationを記録" if feasible else f"{status}をobjectiveなしで記録",
        event_label_en="Record a successful simulation"
        if feasible
        else f"Record {status} without an objective",
        keyframe=True,
        points=[],
        vectors=[],
        metrics=[
            _metric(
                "feasible_rate",
                "feasible rate",
                "feasible rate",
                successes / evaluations,
                "fraction",
            ),
            _metric(
                "successful_evaluations",
                "成功評価数",
                "successful evaluations",
                float(successes),
                "calls",
            ),
            _metric(
                "failed_evaluations",
                "失敗評価数",
                "failed evaluations",
                float(evaluations - successes),
                "calls",
            ),
            _metric(
                "best_feasible_objective",
                "最良feasible objective",
                "best feasible objective",
                best_feasible,
                "objective",
            ),
        ]
        + (
            []
            if value is None
            else [_metric("objective_value", "objective", "objective", value, "objective")]
        ),
        payload={
            "candidate": {"u1": u1, "u2": u2, "mode": mode},
            "evaluation_status": status,
            "objective_value": value,
            "failure_is_penalty_value": False,
            "scope": "deterministic teaching ledger; not a MADS or Nevergrad benchmark",
        },
    )


def generate_failed_simulation_trace(*, dataset_version: str, policy: Policy) -> AlgorithmTrace:
    ledger = [
        (0.65, 0.35, 0, "ok", 0.0),
        (0.15, 0.05, 1, "crash", None),
        (0.45, 0.10, 0, "ok", 0.0625),
        (0.82, 0.62, 1, "timeout", None),
        (0.60, 0.30, 0, "ok", 0.0025),
        (0.70, 0.42, 1, "ok", 0.0933),
    ]
    if policy == "failure":
        ledger[4] = (0.10, 0.08, 0, "nonphysical", None)
    frames = [
        _frame(index=index, u1=u1, u2=u2, mode=mode, status=status, value=value)
        for index, (u1, u2, mode, status, value) in enumerate(ledger)
    ]
    failure = policy == "failure"
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=FAILURE_TRACE_ID if failure else FEASIBLE_TRACE_ID,
        method_id="M_MADS",
        profile_id=PROFILE_ID,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=FAILURE_SCENARIO_ID if failure else FEASIBLE_SCENARIO_ID,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"kind": "successful_simulation_objective", "direction": "minimize"},
        preset={"preset_id": "FAILED_SIMULATION_EC027_FIXED_6"},
        parameters={
            "failure_region": "u1+u2<0.25",
            "failure_policy": "record_status_without_penalty",
            "evaluation_cost": "one_call_per_ledger_row",
        },
        initial_state={
            "point": [0.65, 0.35, 0.0],
            "decision_domain": "two_continuous_plus_binary_mode",
        },
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=6,
        stopping={"oracle_evaluations": 6},
        environment={
            "runtime": "deterministic_educational_failure_ledger",
            "version": GENERATOR_VERSION,
        },
        fairness_statement="Both ledgers share six candidates, the design domain, failure taxonomy, and no-penalty policy; only the fifth candidate status changes.",
        frames=frames,
        terminal_status="failed" if failure else "completed",
        terminal_summary_ja="失敗をobjective penaltyへ置き換えず、成功評価・失敗status・最良feasible objectiveを分けて記録した。",
        terminal_summary_en="Failures remain statuses rather than objective penalties; successful evaluations, failure status, and best feasible objective stay separate.",
        source_ids=["S002", "S018", "S031", "S034", "S035", "S060", "S063"],
    )


def generate_failed_simulation_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    return [
        generate_failed_simulation_trace(dataset_version=dataset_version, policy="feasible"),
        generate_failed_simulation_trace(dataset_version=dataset_version, policy="failure"),
    ]


def _text(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def build_failed_simulation_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    failure = trace.scenario_id == FAILURE_SCENARIO_ID
    counterpart = FEASIBLE_SCENARIO_ID if failure else FAILURE_SCENARIO_ID
    payload = canonical_trace_bytes(trace)
    observables = [
        VisualizationObservable(
            observable_id="feasible_rate", label_ja="feasible rate", label_en="feasible rate"
        ),
        VisualizationObservable(
            observable_id="successful_evaluations",
            label_ja="成功評価数",
            label_en="successful evaluations",
        ),
        VisualizationObservable(
            observable_id="failed_evaluations", label_ja="失敗評価数", label_en="failed evaluations"
        ),
        VisualizationObservable(
            observable_id="best_feasible_objective",
            label_ja="最良feasible objective",
            label_en="best feasible objective",
        ),
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja="失敗simulation: statusを残すfailure ledger"
        if failure
        else "失敗simulation: feasible evaluation ledger",
        title_en="Failed simulation: retain failure status"
        if failure
        else "Failed simulation: feasible evaluation ledger",
        purpose="failure_contrast" if failure else "mechanism",
        problem_definition_id=PROBLEM_DEFINITION_ID,
        problem_instance_id=PROBLEM_INSTANCE_ID,
        lesson=VisualizationLesson(
            learning_objective=_text(
                "成功率、失敗status、最良feasible objectiveを混同せずに読む。",
                "Read feasible rate, failure status, and best feasible objective separately.",
            ),
            misconception=_text(
                "失敗評価を大きい目的値にすれば、同じ最適化履歴として安全に比較できる。",
                "A large synthetic objective makes failed evaluations safely comparable.",
            )
            if failure
            else None,
            expected_phenomenon_ja="失敗はobjectiveを持たず、同じevaluation budgetでもfeasible rateと最良feasible値の意味が変わる。",
            expected_phenomenon_en="Failures have no objective, so feasible rate and best feasible value change meaning under the same evaluation budget.",
            success_signals=[
                VisualizationSignal(
                    signal_id="status_separate",
                    label_ja="failureをobjectiveから分離",
                    label_en="separate failure from objective",
                    observable_ids=[
                        "feasible_rate",
                        "failed_evaluations",
                        "best_feasible_objective",
                    ],
                )
            ],
            failure_signals=[
                VisualizationSignal(
                    signal_id="synthetic_penalty",
                    label_ja="penaltyへ偽装しない",
                    label_en="do not synthesize a penalty",
                    observable_ids=["failed_evaluations", "best_feasible_objective"],
                )
            ]
            if failure
            else [],
            primary_observables=observables[:3],
            secondary_observables=observables[3:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="評価statusを先に見る",
                    title_en="Read evaluation status first",
                    observable_ids=["feasible_rate", "failed_evaluations"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="成功評価だけを集計",
                    title_en="Aggregate successful evaluations only",
                    observable_ids=["successful_evaluations", "best_feasible_objective"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="failureを隠さない",
                    title_en="Keep failure visible",
                    observable_ids=["feasible_rate", "failed_evaluations"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="最良値のscopeを限定",
                    title_en="Bound the scope of the best value",
                    observable_ids=["best_feasible_objective"],
                ),
            ],
            comparison_role="failure_contrast" if failure else "primary_example",
            prerequisite_concept_ids=["concept.black-box-optimization"],
            recommended_next_scenario_ids=[counterpart],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown", note_ja="最適解は表示しない。", note_en="No optimum is shown."
            ),
            static_summary=_text(
                "6回の固定simulation callで、成功とfailureを別ledgerとして読む。",
                "Read success and failure as separate ledgers across six fixed calls.",
            ),
            text_alternative=_text(
                "各callのstatus、成功件数、失敗件数、feasible rate、最良feasible objectiveを列挙する。",
                "List status, successful and failed counts, feasible rate, and best feasible objective for each call.",
            ),
            derived_media_caption=_text(
                "失敗simulationのevaluation ledger", "Evaluation ledger for failed simulations"
            ),
            limitations_ja="決定的な教育用ledgerであり、MADS・Nevergrad・実simulationの性能比較ではない。",
            limitations_en="A deterministic teaching ledger, not a MADS, Nevergrad, or real-simulation benchmark.",
        ),
        guided_story=None,
        experiment=VisualizationExperiment(
            oracle_policy=["objective_value", "constraint_value"],
            initial_condition=VisualizationInitialCondition(point=[0.65, 0.35, 0.0]),
            parameter_preset_id="FAILED_SIMULATION_EC027_FIXED_6",
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=6),
            stopping={"oracle_evaluations": 6},
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id=f"RUN_{trace.trace_id.upper().replace('-', '_')}",
                method_id=trace.method_id,
                profile_id=trace.profile_id,
                implementation_mapping_status=trace.implementation_mapping_status,
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
