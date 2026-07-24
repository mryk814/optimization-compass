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

GENERATOR_ID = "educational.time_window_routing.v1"
GENERATOR_VERSION = "1.0.0"
PROFILE_ID = "PROFILE_TIME_WINDOW_ROUTING"
PROBLEM_DEFINITION_ID = "PROBLEM_TIME_WINDOW_ROUTING"
PROBLEM_INSTANCE_ID = "INSTANCE_TIME_WINDOW_ROUTING_EC019"
FEASIBLE_SCENARIO_ID = "SCENARIO_TIME_WINDOW_ROUTING_FEASIBLE"
VIOLATION_SCENARIO_ID = "SCENARIO_TIME_WINDOW_ROUTING_VIOLATION"
FEASIBLE_TRACE_ID = "time-window-routing-feasible"
VIOLATION_TRACE_ID = "time-window-routing-violation"

WindowPolicy = Literal["feasible", "violation"]


def _localized(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def _metric(metric_id: str, ja: str, en: str, value: float, unit: str) -> TraceMetric:
    return TraceMetric(metric_id=metric_id, label_ja=ja, label_en=en, value=value, unit=unit)


def _frame(
    *,
    index: int,
    stop: int,
    arrival: float,
    window_end: float,
    travel_total: float,
    policy: WindowPolicy,
) -> TraceFrame:
    violation = max(0.0, arrival - window_end)
    return TraceFrame(
        frame_index=index,
        iteration=index,
        oracle_evaluations=index + 1,
        elapsed_steps=index,
        elapsed_time_ms=travel_total * 60_000.0,
        event_type="initialize" if index == 0 else "update" if index < 4 else "stop",
        decision="not_applicable" if index == 0 else "accepted" if violation == 0 else "rejected",
        explanation_key="time_window_route_ledger",
        event_label_ja=(
            "depotを出発"
            if index == 0
            else f"stop {stop}の時間窓を確認"
            if index < 4
            else "depotへ帰着して固定routeを終了"
        ),
        event_label_en=(
            "Leave the depot"
            if index == 0
            else f"Check the time window at stop {stop}"
            if index < 4
            else "Return to the depot and stop the fixed route"
        ),
        keyframe=True,
        points=[],
        vectors=[],
        metrics=[
            _metric("arrival_time", "到着時刻", "arrival time", arrival, "minutes"),
            _metric("window_end", "時間窓の終了", "time-window end", window_end, "minutes"),
            _metric(
                "window_violation", "時間窓違反", "time-window violation", violation, "minutes"
            ),
            _metric(
                "cumulative_travel_time",
                "累積移動時間",
                "cumulative travel time",
                travel_total,
                "minutes",
            ),
            _metric(
                "route_feasibility",
                "route可行性",
                "route feasibility",
                1.0 if violation == 0 else 0.0,
                "status",
            ),
        ],
        payload={
            "route": [0, 1, 2, 3, 4, 0],
            "current_stop": stop,
            "arrival_time": arrival,
            "time_window": [0, window_end],
            "time_window_violation": violation,
            "window_policy": policy,
            "scope": "fixed-route deterministic teaching ledger; not an OR-Tools execution benchmark",
        },
    )


def generate_time_window_routing_trace(
    *, dataset_version: str, policy: WindowPolicy
) -> AlgorithmTrace:
    # The same route and travel-time matrix are used for both traces.  Only stop 4's
    # latest permitted arrival changes, making constraint violation visible without
    # turning it into an optimizer performance claim.
    window_ends = [30.0, 10.0, 15.0, 20.0, 25.0 if policy == "feasible" else 12.0, 30.0]
    stops = [0, 1, 2, 3, 4, 0]
    arrivals = [0.0, 4.0, 7.0, 11.0, 14.0, 21.0]
    frames = [
        _frame(
            index=index,
            stop=stop,
            arrival=arrival,
            window_end=window_end,
            travel_total=arrival,
            policy=policy,
        )
        for index, (stop, arrival, window_end) in enumerate(
            zip(stops, arrivals, window_ends, strict=True)
        )
    ]
    is_violation = policy == "violation"
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=VIOLATION_TRACE_ID if is_violation else FEASIBLE_TRACE_ID,
        method_id="M_LOCAL_SEARCH_COMBINATORIAL",
        profile_id=PROFILE_ID,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=VIOLATION_SCENARIO_ID if is_violation else FEASIBLE_SCENARIO_ID,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"kind": "fixed_route_travel_time", "route": [0, 1, 2, 3, 4, 0]},
        preset={"preset_id": "TIME_WINDOW_ROUTING_FIXED_4_STOP", "vehicle_count": 1},
        parameters={
            "travel_time_matrix": "fixed_5_by_5_minutes",
            "route": [0, 1, 2, 3, 4, 0],
            "vehicle_count": 1,
            "changed_window": "stop_4_latest_arrival" if is_violation else "none",
            "hard_constraint_policy": "do_not_penalize_time_window_violation",
        },
        initial_state={"point": [1.0, 2.0, 3.0, 4.0], "decision_domain": "stop_permutation"},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=6,
        stopping={"route_legs": 5, "oracle_evaluations": 6},
        environment={
            "runtime": "deterministic_educational_route_ledger",
            "version": GENERATOR_VERSION,
        },
        fairness_statement=(
            "Both members use the same depot, one vehicle, four-stop route, travel-time matrix, "
            "start time, and all other windows; only stop 4's latest arrival changes."
        ),
        frames=frames,
        terminal_status="failed" if is_violation else "completed",
        terminal_summary_ja=(
            "stop 4への到着14分が終了12分を2分超えたため、固定routeは時間窓hard constraintを満たさない。"
            if is_violation
            else "固定routeは4 stopを各1回訪問し、全ての時間窓内に到着して21分でdepotへ帰着した。"
        ),
        terminal_summary_en=(
            "Arrival at stop 4 is 14 minutes, two minutes after its 12-minute latest arrival, "
            "so the fixed route violates the hard time window."
            if is_violation
            else "The fixed route visits all four stops once, reaches every stop inside its time "
            "window, and returns to the depot after 21 minutes."
        ),
        source_ids=["S022", "S023", "S024", "S079"],
    )


def generate_time_window_routing_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    return [
        generate_time_window_routing_trace(dataset_version=dataset_version, policy="feasible"),
        generate_time_window_routing_trace(dataset_version=dataset_version, policy="violation"),
    ]


def build_time_window_routing_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    is_violation = trace.scenario_id == VIOLATION_SCENARIO_ID
    counterpart = FEASIBLE_SCENARIO_ID if is_violation else VIOLATION_SCENARIO_ID
    payload = canonical_trace_bytes(trace)
    observables = [
        VisualizationObservable(
            observable_id="arrival_time", label_ja="到着時刻", label_en="arrival time"
        ),
        VisualizationObservable(
            observable_id="window_end", label_ja="時間窓の終了", label_en="time-window end"
        ),
        VisualizationObservable(
            observable_id="window_violation",
            label_ja="時間窓違反",
            label_en="time-window violation",
        ),
        VisualizationObservable(
            observable_id="cumulative_travel_time",
            label_ja="累積移動時間",
            label_en="cumulative travel time",
        ),
        VisualizationObservable(
            observable_id="route_feasibility",
            label_ja="route可行性",
            label_en="route feasibility",
        ),
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja="時間窓付き配送: stop 4で違反を検出"
        if is_violation
        else "時間窓付き配送: 固定routeの可行性",
        title_en="Time-window routing: detect a violation at stop 4"
        if is_violation
        else "Time-window routing: feasibility of a fixed route",
        purpose="failure_contrast" if is_violation else "mechanism",
        problem_definition_id=PROBLEM_DEFINITION_ID,
        problem_instance_id=PROBLEM_INSTANCE_ID,
        lesson=VisualizationLesson(
            learning_objective=_localized(
                "到着時刻、時間窓、累積移動時間、可行性を別々に読む。",
                "Read arrival time, time windows, cumulative travel time, and feasibility separately.",
            ),
            misconception=_localized(
                "時間窓違反を目的値の小さな差やpenaltyだけで扱えば、routeは実行可能といえる。",
                "A small objective change or penalty is enough to call a route time-window feasible.",
            )
            if is_violation
            else None,
            expected_phenomenon_ja="同じrouteでもstop 4の終了時刻だけを狭めると、到着14分は不変のまま時間窓違反が2分になる。",
            expected_phenomenon_en="With the same route, narrowing only stop 4's latest arrival leaves the 14-minute arrival unchanged and creates a two-minute violation.",
            success_signals=[
                VisualizationSignal(
                    signal_id="arrival_window_separated",
                    label_ja="到着と時間窓を分けて確認できる",
                    label_en="arrival and time window remain separate",
                    observable_ids=[
                        "arrival_time",
                        "window_end",
                        "window_violation",
                        "route_feasibility",
                    ],
                )
            ],
            failure_signals=[
                VisualizationSignal(
                    signal_id="hard_window_violation",
                    label_ja="stop 4の時間窓違反を見落とさない",
                    label_en="do not overlook the stop-4 time-window violation",
                    observable_ids=["arrival_time", "window_end", "window_violation"],
                )
            ]
            if is_violation
            else [],
            primary_observables=observables[:3],
            secondary_observables=observables[3:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="固定routeと時間行列を確認",
                    title_en="Inspect the fixed route and travel-time matrix",
                    observable_ids=["arrival_time", "cumulative_travel_time"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="stopごとの到着を追う",
                    title_en="Follow arrivals by stop",
                    observable_ids=["arrival_time", "window_end"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="stop 4の2分違反を読む",
                    title_en="Read the two-minute stop-4 violation",
                    observable_ids=["arrival_time", "window_end", "window_violation"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="可行性と総移動時間を混同しない",
                    title_en="Do not conflate feasibility and total travel time",
                    observable_ids=["route_feasibility", "cumulative_travel_time"],
                ),
            ],
            comparison_role="failure_contrast" if is_violation else "primary_example",
            prerequisite_concept_ids=["concept.combinatorial-optimization"],
            recommended_next_scenario_ids=[counterpart],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="この教材では最適routeを表示しない。固定routeの時間窓診断だけを表示する。",
                note_en="No optimal route is shown; the lesson only diagnoses time windows for a fixed route.",
            ),
            static_summary=_localized(
                "4 stop・1車両の固定routeで、到着時刻と時間窓を順に照合する。",
                "Check arrivals against time windows along one fixed four-stop route.",
            ),
            text_alternative=_localized(
                "depotからstop 1、2、3、4を経てdepotへ戻るrouteについて、各stopの到着と終了時刻、違反、累積移動時間を列挙する。",
                "For the depot–1–2–3–4–depot route, list each arrival, window end, violation, and cumulative travel time.",
            ),
            derived_media_caption=_localized(
                "時間窓付き配送routeの到着・違反ledger",
                "Arrival and violation ledger for a time-window route",
            ),
            limitations_ja="固定行列・4 stop・1車両・service timeなしの決定的教材であり、OR-Tools実行、local searchの性能、交通予測、複数車両割当、容量、休憩、実道路の到着保証を示さない。",
            limitations_en="A deterministic four-stop, one-vehicle lesson without service time; it does not measure OR-Tools or local-search performance, traffic forecasts, multi-vehicle assignment, capacity, breaks, or real-road arrival guarantees.",
        ),
        guided_story=None,
        experiment=VisualizationExperiment(
            oracle_policy=["objective_value", "constraint_value"],
            initial_condition=VisualizationInitialCondition(point=[1.0, 2.0, 3.0, 4.0]),
            parameter_preset_id="TIME_WINDOW_ROUTING_FIXED_4_STOP",
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=6),
            stopping={"route_legs": 5, "oracle_evaluations": 6},
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
