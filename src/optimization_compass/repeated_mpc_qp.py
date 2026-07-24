from __future__ import annotations

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

GENERATOR_ID = "educational.repeated_mpc_qp.v1"
GENERATOR_VERSION = "1.0.0"
PROFILE_ID = "PROFILE_REPEATED_MPC_QP"
PROBLEM_DEFINITION_ID = "PROBLEM_OPTIMAL_CONTROL"
PROBLEM_INSTANCE_ID = "INSTANCE_REPEATED_MPC_QP_EC025"
WARM_SCENARIO_ID = "SCENARIO_REPEATED_MPC_QP_WARM_START"
COLD_SCENARIO_ID = "SCENARIO_REPEATED_MPC_QP_COLD_START"
WARM_TRACE_ID = "repeated-mpc-qp-warm-start"
COLD_TRACE_ID = "repeated-mpc-qp-cold-start"

Policy = Literal["warm", "cold"]


def _localized(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def _metric(metric_id: str, ja: str, en: str, value: float, unit: str) -> TraceMetric:
    return TraceMetric(
        metric_id=metric_id,
        label_ja=ja,
        label_en=en,
        value=value,
        unit=unit,
    )


def _frame(
    *,
    index: int,
    state: float,
    control: float,
    iterations: int,
    solve_time_ms: float,
    elapsed_time_ms: float,
    primal_residual: float,
    dual_residual: float,
    deadline_ms: float,
    policy: Policy,
) -> TraceFrame:
    deadline_margin_ms = deadline_ms - solve_time_ms
    return TraceFrame(
        frame_index=index,
        iteration=index,
        oracle_evaluations=index + 1,
        elapsed_steps=index,
        elapsed_time_ms=elapsed_time_ms,
        event_type="initialize" if index == 0 else "update" if index < 3 else "stop",
        decision="not_applicable" if index == 0 else "accepted",
        explanation_key=("cold_start_qp" if policy == "cold" else "warm_start_qp"),
        event_label_ja=(
            "初回QPを解く" if index == 0 else "次周期のQPを解く" if index < 3 else "4周期で固定停止"
        ),
        event_label_en=(
            "Solve the initial QP"
            if index == 0
            else "Solve the next-cycle QP"
            if index < 3
            else "Stop after four cycles"
        ),
        keyframe=True,
        points=[],
        vectors=[],
        metrics=[
            _metric("tracking_error", "追従誤差", "tracking error", abs(1.0 - state), "state"),
            _metric("control_effort", "操作量", "control effort", abs(control), "input"),
            _metric(
                "primal_residual", "primal残差", "primal residual", primal_residual, "residual"
            ),
            _metric("dual_residual", "dual残差", "dual residual", dual_residual, "residual"),
            _metric(
                "solver_iterations",
                "solver反復",
                "solver iterations",
                float(iterations),
                "iterations",
            ),
            _metric("solve_time_ms", "解時間ledger", "solve-time ledger", solve_time_ms, "ms"),
            _metric(
                "deadline_margin_ms", "deadline余裕", "deadline margin", deadline_margin_ms, "ms"
            ),
        ],
        payload={
            "cycle": index,
            "x_current": state,
            "u_applied": control,
            "warm_start": policy == "warm" and index > 0,
            "deadline_ms": deadline_ms,
            "deadline_status": "met" if deadline_margin_ms >= 0 else "missed",
            "timing_scope": (
                "deterministic educational iteration-to-latency ledger; not hardware measurement"
            ),
        },
    )


def generate_repeated_mpc_qp_trace(*, dataset_version: str, policy: Policy) -> AlgorithmTrace:
    # The state and residual ledgers are fixed teaching data.  The latency values are
    # deliberately a reproducible iteration-to-latency model, not an OSQP benchmark.
    common = [
        (0.00, 0.40, 64, 3.20, 8e-6, 7e-6),
        (
            0.40,
            0.24,
            54 if policy == "cold" else 28,
            2.70 if policy == "cold" else 1.40,
            6e-6,
            5e-6,
        ),
        (
            0.64,
            0.14,
            48 if policy == "cold" else 22,
            2.40 if policy == "cold" else 1.10,
            5e-6,
            4e-6,
        ),
        (
            0.78,
            0.08,
            44 if policy == "cold" else 20,
            2.20 if policy == "cold" else 1.00,
            4e-6,
            4e-6,
        ),
    ]
    scenario_id = WARM_SCENARIO_ID if policy == "warm" else COLD_SCENARIO_ID
    trace_id = WARM_TRACE_ID if policy == "warm" else COLD_TRACE_ID
    deadline_ms = 3.0
    elapsed_time_ms = 0.0
    frames = []
    for index, (
        state,
        control,
        iterations,
        solve_time_ms,
        primal_residual,
        dual_residual,
    ) in enumerate(common):
        elapsed_time_ms += solve_time_ms
        frames.append(
            _frame(
                index=index,
                state=state,
                control=control,
                iterations=iterations,
                solve_time_ms=solve_time_ms,
                elapsed_time_ms=elapsed_time_ms,
                primal_residual=primal_residual,
                dual_residual=dual_residual,
                deadline_ms=deadline_ms,
                policy=policy,
            )
        )
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id,
        method_id="M_ADMM_QP",
        profile_id=PROFILE_ID,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=scenario_id,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"kind": "finite_horizon_tracking_plus_control_effort", "horizon": 4},
        preset={"preset_id": "REPEATED_MPC_QP_FIXED_H4", "deadline_ms": deadline_ms},
        parameters={
            "horizon": 4,
            "state_dimension": 1,
            "control_dimension": 1,
            "deadline_ms": deadline_ms,
            "latency_model": "deterministic_iteration_to_latency_ledger",
            "warm_start_policy": policy,
        },
        initial_state={"point": [0.0], "reference": 1.0},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=4,
        stopping={"control_cycles": 4, "deadline_ms": deadline_ms},
        environment={"runtime": "deterministic_educational_ledger", "version": GENERATOR_VERSION},
        fairness_statement=(
            "Both members use the same scalar dynamics, horizon, bounds, reference, "
            "residual ledger, three-millisecond deadline policy, and four control cycles; "
            "only warm-start reuse changes."
        ),
        frames=frames,
        terminal_status="completed",
        terminal_summary_ja=(
            "4周期の固定MPC QP ledgerを完了した。warm startは初回解を速くせず、"
            "第2周期以降の反復とdeadline余裕を読む対象にする。"
        ),
        terminal_summary_en=(
            "The four-cycle fixed MPC QP ledger completed. Warm starting does not accelerate the "
            "initial solve; it changes the iteration and deadline margin from the second cycle."
        ),
        source_ids=["S012", "S043", "S076"],
    )


def generate_repeated_mpc_qp_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    return [
        generate_repeated_mpc_qp_trace(dataset_version=dataset_version, policy="warm"),
        generate_repeated_mpc_qp_trace(dataset_version=dataset_version, policy="cold"),
    ]


def build_repeated_mpc_qp_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    is_cold = trace.scenario_id == COLD_SCENARIO_ID
    counterpart = WARM_SCENARIO_ID if is_cold else COLD_SCENARIO_ID
    payload = canonical_trace_bytes(trace)
    observables = [
        VisualizationObservable(
            observable_id="tracking_error", label_ja="追従誤差", label_en="tracking error"
        ),
        VisualizationObservable(
            observable_id="primal_residual", label_ja="primal残差", label_en="primal residual"
        ),
        VisualizationObservable(
            observable_id="dual_residual", label_ja="dual残差", label_en="dual residual"
        ),
        VisualizationObservable(
            observable_id="solver_iterations", label_ja="solver反復", label_en="solver iterations"
        ),
        VisualizationObservable(
            observable_id="solve_time_ms", label_ja="解時間ledger", label_en="solve-time ledger"
        ),
        VisualizationObservable(
            observable_id="deadline_margin_ms", label_ja="deadline余裕", label_en="deadline margin"
        ),
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja="反復MPC QP: cold startのdeadline ledger"
        if is_cold
        else "反復MPC QP: warm startのdeadline ledger",
        title_en="Repeated MPC QP: cold-start deadline ledger"
        if is_cold
        else "Repeated MPC QP: warm-start deadline ledger",
        purpose="sensitivity" if is_cold else "mechanism",
        problem_definition_id=PROBLEM_DEFINITION_ID,
        problem_instance_id=PROBLEM_INSTANCE_ID,
        lesson=VisualizationLesson(
            learning_objective=_localized(
                "追従誤差、QP残差、反復数、deadline余裕を制御周期ごとに分けて読む。",
                "Read tracking error, QP residuals, iterations, and deadline margin "
                "separately by control cycle.",
            ),
            misconception=(
                _localized(
                    "warm startを使えば初回から必ずdeadlineを満たし、残差確認も不要になる。",
                    "Warm starting always meets the deadline from the first cycle and "
                    "removes the need to inspect residuals.",
                )
                if is_cold
                else None
            ),
            expected_phenomenon_ja=(
                "初回は共通でも、第2周期以降はwarm startの有無で反復数とdeadline余裕が変わる。"
            ),
            expected_phenomenon_en=(
                "The initial solve is shared, while warm-start reuse changes iterations "
                "and deadline margin from the second cycle."
            ),
            success_signals=[
                VisualizationSignal(
                    signal_id="residual_and_deadline_separated",
                    label_ja="残差とdeadline余裕を別々に確認できる",
                    label_en="residuals and deadline margin remain separate",
                    observable_ids=["primal_residual", "dual_residual", "deadline_margin_ms"],
                )
            ],
            failure_signals=(
                [
                    VisualizationSignal(
                        signal_id="deadline_miss_under_cold_start",
                        label_ja="cold start ledgerではdeadline余裕が負になる周期が残る",
                        label_en="the cold-start ledger retains a negative deadline margin",
                        observable_ids=["solver_iterations", "solve_time_ms", "deadline_margin_ms"],
                    )
                ]
                if is_cold
                else []
            ),
            primary_observables=observables[:3],
            secondary_observables=observables[3:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="共通のQP契約を確認",
                    title_en="Inspect the shared QP contract",
                    observable_ids=["tracking_error", "primal_residual"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="第2周期のwarm start差を見る",
                    title_en="Read the second-cycle warm-start difference",
                    observable_ids=["solver_iterations", "solve_time_ms"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="残差とdeadline余裕を分ける",
                    title_en="Separate residuals from deadline margin",
                    observable_ids=["primal_residual", "dual_residual", "deadline_margin_ms"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="実測範囲を限定する",
                    title_en="Bound the measurement claim",
                    observable_ids=["solve_time_ms", "deadline_margin_ms"],
                ),
            ],
            comparison_role="sensitivity_variant" if is_cold else "primary_example",
            prerequisite_concept_ids=["concept.receding-horizon"],
            recommended_next_scenario_ids=[counterpart],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="実機のworst-case解時間や閉loop安定性の既知値は表示しない。",
                note_en=(
                    "No known worst-case hardware timing or closed-loop stability "
                    "reference is shown."
                ),
            ),
            static_summary=_localized(
                "4周期の固定QPで、追従誤差、残差、反復数、解時間ledger、deadline余裕を並べる。",
                "Align tracking error, residuals, iterations, a solve-time ledger, and "
                "deadline margin across four fixed QPs.",
            ),
            text_alternative=_localized(
                "各周期についてwarm-start有無、primal/dual残差、反復数、3ms deadlineに"
                "対する余裕を列挙する。",
                "For each cycle, list warm-start status, primal/dual residuals, iterations, "
                "and margin against the three-millisecond deadline.",
            ),
            derived_media_caption=_localized(
                "反復MPC QPのresidualとdeadline ledger",
                "Repeated MPC QP residual and deadline ledger",
            ),
            limitations_ja="決定的なiteration-to-latency教材であり、OSQPやADMMの実CPU時間、100Hz達成、閉loop安定性、安全性、一般的性能順位を示さない。",
            limitations_en=(
                "A deterministic iteration-to-latency lesson; it does not establish OSQP or "
                "ADMM CPU time, 100-Hz operation, closed-loop stability, safety, or a general "
                "performance ranking."
            ),
        ),
        guided_story=None,
        experiment=VisualizationExperiment(
            oracle_policy=["objective_value", "constraint_value", "constraint_jacobian"],
            initial_condition=VisualizationInitialCondition(point=[0.0]),
            parameter_preset_id="REPEATED_MPC_QP_FIXED_H4",
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=4),
            stopping={"control_cycles": 4, "deadline_ms": 3.0},
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
            observable_ids=[item.observable_id for item in observables],
            payload_path=f"traces/{trace.trace_id}.json",
            payload_bytes=len(payload),
            payload_sha256=sha256(payload).hexdigest(),
        ),
        source_ids=trace.source_ids,
        last_verified="2026-07-24",
    )
