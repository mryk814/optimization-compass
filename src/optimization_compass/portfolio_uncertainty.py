from __future__ import annotations

from hashlib import sha256
from itertools import product
from typing import Literal

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
)

GENERATOR_ID = "educational.portfolio_uncertainty.v1"
GENERATOR_VERSION = "1.0.0"
PROFILE_ID = "PROFILE_PORTFOLIO_UNCERTAINTY"
PROBLEM_DEFINITION_ID = "PROBLEM_PORTFOLIO_UNCERTAINTY"
PROBLEM_INSTANCE_ID = "INSTANCE_PORTFOLIO_CVAR_FIXED_8_4"
NOMINAL_SCENARIO_ID = "SCENARIO_PORTFOLIO_NOMINAL_8_4"
CVAR_SCENARIO_ID = "SCENARIO_PORTFOLIO_CVAR_8_4"
NOMINAL_TRACE_ID = "portfolio-nominal-8-4"
CVAR_TRACE_ID = "portfolio-cvar-8-4"

Policy = Literal["nominal", "cvar"]

TRAIN_RETURNS = (
    (0.08, 0.02, -0.01, 0.04),
    (-0.03, 0.05, 0.01, 0.02),
    (0.04, -0.02, 0.03, 0.01),
    (0.01, 0.00, -0.04, 0.03),
    (-0.06, 0.03, -0.02, 0.01),
    (0.02, -0.04, 0.02, 0.00),
    (0.03, 0.01, 0.00, -0.05),
    (-0.02, 0.02, 0.04, 0.01),
)
HELD_OUT_RETURNS = (
    (0.01, 0.00, -0.02, 0.03),
    (-0.04, 0.02, 0.01, 0.00),
    (0.02, -0.01, 0.02, -0.03),
    (0.00, 0.03, -0.01, 0.02),
)
ALPHA = 0.75
RISK_WEIGHT = 0.5
GRID_DENOMINATOR = 20
MAX_WEIGHT_UNITS = 12


def _localized(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def _losses(
    returns: tuple[tuple[float, ...], ...], weights: tuple[float, ...]
) -> tuple[float, ...]:
    return tuple(
        -sum(value * weight for value, weight in zip(row, weights, strict=True)) for row in returns
    )


def _mean(values: tuple[float, ...]) -> float:
    return sum(values) / len(values)


def _empirical_cvar(values: tuple[float, ...]) -> float:
    tail_count = max(1, round((1.0 - ALPHA) * len(values)))
    return _mean(tuple(sorted(values, reverse=True)[:tail_count]))


def _candidate_weights() -> list[tuple[float, ...]]:
    units = range(MAX_WEIGHT_UNITS + 1)
    return [
        tuple(value / GRID_DENOMINATOR for value in candidate)
        for candidate in product(units, repeat=4)
        if sum(candidate) == GRID_DENOMINATOR
    ]


def _select_weights(policy: Policy) -> tuple[float, ...]:
    risk_weight = 0.0 if policy == "nominal" else RISK_WEIGHT

    def objective(weights: tuple[float, ...]) -> tuple[float, tuple[float, ...]]:
        losses = _losses(TRAIN_RETURNS, weights)
        value = _mean(losses) + risk_weight * _empirical_cvar(losses)
        return value, weights

    return min(_candidate_weights(), key=objective)


def _metric(metric_id: str, ja: str, en: str, value: float) -> TraceMetric:
    return TraceMetric(
        metric_id=metric_id,
        label_ja=ja,
        label_en=en,
        value=round(value, 12),
        unit="loss",
    )


def _summary_metrics(losses: tuple[float, ...]) -> list[TraceMetric]:
    return [
        _metric("mean_loss", "平均loss", "mean loss", _mean(losses)),
        _metric("cvar_75", "CVaR 75%", "CVaR 75%", _empirical_cvar(losses)),
        _metric("worst_loss", "最大loss", "worst loss", max(losses)),
        _metric("best_loss", "最小loss", "best loss", min(losses)),
    ]


def _frame(
    *,
    frame_index: int,
    evaluations: int,
    split: Literal["initial", "training", "held_out"],
    weights: tuple[float, ...],
    losses: tuple[float, ...] | None,
) -> TraceFrame:
    labels = {
        "initial": ("比較条件を固定", "Fix comparison contract"),
        "training": ("training scenarioを集計", "Summarize training scenarios"),
        "held_out": ("held-out scenarioで再評価", "Evaluate held-out scenarios"),
    }
    ja, en = labels[split]
    return TraceFrame(
        frame_index=frame_index,
        iteration=frame_index,
        oracle_evaluations=evaluations,
        elapsed_steps=frame_index,
        elapsed_time_ms=float(frame_index * 100),
        event_type="initialize"
        if split == "initial"
        else "out_of_sample_check"
        if split == "held_out"
        else "scenario_batch",
        decision="not_applicable",
        explanation_key="fixed_contract" if split == "initial" else split,
        event_label_ja=ja,
        event_label_en=en,
        keyframe=True,
        points=[
            TracePoint(
                point_id="portfolio_weights",
                role="decision",
                coordinates=list(weights),
                value=None,
                label_ja="固定した配分vector",
                label_en="fixed allocation vector",
            )
        ],
        vectors=[],
        metrics=[] if losses is None else _summary_metrics(losses),
        payload={
            "split": split,
            "sample_count": 0 if losses is None else len(losses),
            "losses": [] if losses is None else [round(value, 12) for value in losses],
            "weights": list(weights),
            "alpha": ALPHA,
            "risk_weight": RISK_WEIGHT,
            "claim_scope": "fixed_empirical_scenarios_only",
        },
    )


def generate_portfolio_uncertainty_trace(*, dataset_version: str, policy: Policy) -> AlgorithmTrace:
    weights = _select_weights(policy)
    train_losses = _losses(TRAIN_RETURNS, weights)
    held_out_losses = _losses(HELD_OUT_RETURNS, weights)
    scenario_id = NOMINAL_SCENARIO_ID if policy == "nominal" else CVAR_SCENARIO_ID
    trace_id = NOMINAL_TRACE_ID if policy == "nominal" else CVAR_TRACE_ID
    objective = (
        "training mean loss" if policy == "nominal" else "training mean loss + 0.5 CVaR_0.75"
    )
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version=dataset_version,
        data_version="1.0.0",
        trace_id=trace_id,
        method_id="MF_LP_QP_CONIC",
        profile_id=PROFILE_ID,
        objective_id=PROBLEM_INSTANCE_ID,
        scenario_id=scenario_id,
        generator_id=GENERATOR_ID,
        generator_version=GENERATOR_VERSION,
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={
            "policy": policy,
            "definition": objective,
            "alpha": ALPHA,
            "risk_weight": RISK_WEIGHT,
        },
        preset={
            "preset_id": f"PORTFOLIO_{policy.upper()}_FIXED_8_4",
            "grid_step": 1 / GRID_DENOMINATOR,
        },
        parameters={
            "uncertainty_model": "fixed_return_scenarios",
            "training_sample_count": len(TRAIN_RETURNS),
            "held_out_sample_count": len(HELD_OUT_RETURNS),
            "sample_policy": "fixed_disjoint_8_training_4_held_out",
            "risk_level": ALPHA,
            "confidence_target": "not_applicable_no_probability_guarantee",
            "max_asset_weight": MAX_WEIGHT_UNITS / GRID_DENOMINATOR,
        },
        initial_state={"point": list(weights), "decision_domain": "four_asset_capped_simplex"},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=len(TRAIN_RETURNS) + len(HELD_OUT_RETURNS),
        stopping={"policy": "evaluate_fixed_training_then_held_out", "oracle_evaluations": 12},
        environment={"runtime": "deterministic_educational_grid", "version": GENERATOR_VERSION},
        fairness_statement=(
            "Both policies use the same four-asset capped simplex, eight training returns, "
            "four held-out returns, alpha, sample order, grid, and twelve loss evaluations; "
            "only the training objective risk treatment changes."
        ),
        frames=[
            _frame(frame_index=0, evaluations=0, split="initial", weights=weights, losses=None),
            _frame(
                frame_index=1,
                evaluations=len(TRAIN_RETURNS),
                split="training",
                weights=weights,
                losses=train_losses,
            ),
            _frame(
                frame_index=2,
                evaluations=len(TRAIN_RETURNS) + len(HELD_OUT_RETURNS),
                split="held_out",
                weights=weights,
                losses=held_out_losses,
            ),
        ],
        terminal_status="completed",
        terminal_summary_ja=(
            "固定training 8件で配分を決め、解を変更せずheld-out 4件の"
            "mean・CVaR・worst/best lossを再集計した。"
        ),
        terminal_summary_en=(
            "The allocation was selected on eight fixed training scenarios and then held fixed "
            "while mean, CVaR, worst, and best loss were summarized on four held-out scenarios."
        ),
        source_ids=["S010", "S055"],
    )


def generate_portfolio_uncertainty_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    return [
        generate_portfolio_uncertainty_trace(dataset_version=dataset_version, policy="nominal"),
        generate_portfolio_uncertainty_trace(dataset_version=dataset_version, policy="cvar"),
    ]


def build_portfolio_uncertainty_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    is_cvar = trace.scenario_id == CVAR_SCENARIO_ID
    counterpart = NOMINAL_SCENARIO_ID if is_cvar else CVAR_SCENARIO_ID
    payload = canonical_trace_bytes(trace)
    observables = [
        VisualizationObservable(
            observable_id="mean_loss", label_ja="平均loss", label_en="mean loss"
        ),
        VisualizationObservable(observable_id="cvar_75", label_ja="CVaR 75%", label_en="CVaR 75%"),
        VisualizationObservable(
            observable_id="worst_loss", label_ja="最大loss", label_en="worst loss"
        ),
        VisualizationObservable(
            observable_id="best_loss", label_ja="最小loss", label_en="best loss"
        ),
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja="CVaR配分のtraining / held-out診断"
        if is_cvar
        else "nominal配分のtraining / held-out診断",
        title_en="CVaR allocation: training / held-out diagnostics"
        if is_cvar
        else "Nominal allocation: training / held-out diagnostics",
        purpose="comparison",
        problem_definition_id=PROBLEM_DEFINITION_ID,
        problem_instance_id=PROBLEM_INSTANCE_ID,
        lesson=VisualizationLesson(
            learning_objective=_localized(
                "同じ配分をtrainingとheld-outで評価し、"
                "in-sampleのrisk低下を将来保証と読み替えない。",
                "Evaluate one allocation on training and held-out samples without turning "
                "in-sample risk reduction into a future guarantee.",
            ),
            misconception=_localized(
                "training CVaRが小さければout-of-sampleでも同じ順位になる。",
                "Lower training CVaR guarantees the same out-of-sample ordering.",
            ),
            expected_phenomenon_ja=(
                "training 8件とheld-out 4件でmean・tail・worst/best lossが変わり、"
                "sample依存性が見える。"
            ),
            expected_phenomenon_en=(
                "Mean, tail, worst, and best loss change between eight training and four "
                "held-out scenarios, exposing sample dependence."
            ),
            success_signals=[
                VisualizationSignal(
                    signal_id="split_visible",
                    label_ja="trainingとheld-outを別集計できる",
                    label_en="training and held-out summaries remain separate",
                    observable_ids=["mean_loss", "cvar_75", "worst_loss", "best_loss"],
                )
            ],
            failure_signals=[],
            primary_observables=observables[:3],
            secondary_observables=observables[3:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="共通sample契約を確認",
                    title_en="Inspect the shared sample contract",
                    observable_ids=["mean_loss", "cvar_75"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="training集計を読む",
                    title_en="Read the training summary",
                    observable_ids=["mean_loss", "cvar_75", "worst_loss"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="held-outで差を読む",
                    title_en="Read the held-out shift",
                    observable_ids=["mean_loss", "cvar_75", "worst_loss", "best_loss"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="claim scopeを限定",
                    title_en="Bound the claim scope",
                    observable_ids=["mean_loss", "cvar_75"],
                ),
            ],
            comparison_role="primary_example" if is_cvar else "baseline",
            prerequisite_concept_ids=[
                "concept.uncertainty-models",
                "concept.chance-risk-contract",
                "concept.simplex",
            ],
            recommended_next_scenario_ids=[counterpart],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="母集団riskの既知値はなく、固定sampleのempirical summaryだけを表示する。",
                note_en=(
                    "Population risk is unknown; only empirical summaries of the fixed "
                    "samples are shown."
                ),
            ),
            static_summary=_localized(
                "固定配分のtraining / held-out mean、CVaR、worst/best lossを"
                "12回のloss評価軸で読む。",
                "Read training and held-out mean, CVaR, worst, and best loss for one fixed "
                "allocation over twelve loss evaluations.",
            ),
            text_alternative=_localized(
                "evaluation 8でtraining 8件、evaluation 12で"
                "独立したheld-out 4件のsummaryを表示する。",
                "Evaluation 8 reports eight training scenarios; evaluation 12 reports four "
                "disjoint held-out scenarios.",
            ),
            derived_media_caption=_localized(
                "portfolio allocation: trainingとheld-outのempirical risk",
                "Portfolio allocation: empirical training and held-out risk",
            ),
            limitations_ja=(
                "固定8/4件の教材であり、confidence interval、母集団risk、"
                "将来returnへの保証を与えない。"
            ),
            limitations_en=(
                "A fixed 8/4 teaching sample that provides no confidence interval, "
                "population-risk statement, or guarantee for future returns."
            ),
        ),
        guided_story=None,
        experiment=VisualizationExperiment(
            oracle_policy=["objective_value"],
            initial_condition=VisualizationInitialCondition(
                point=trace.frames[0].points[0].coordinates
            ),
            parameter_preset_id=str(trace.preset["preset_id"]),
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=12),
            stopping={"oracle_evaluations": 12},
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
        last_verified="2026-07-19",
    )
