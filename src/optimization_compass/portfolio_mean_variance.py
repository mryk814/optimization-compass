# ruff: noqa: E501

from __future__ import annotations

from hashlib import sha256
from itertools import product
from typing import Literal, cast

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
)

GENERATOR_ID = "educational.portfolio_mean_variance.v1"
GENERATOR_VERSION = "1.0.0"
PROFILE_ID = "PROFILE_PORTFOLIO_MEAN_VARIANCE"
PROBLEM_DEFINITION_ID = "PROBLEM_PORTFOLIO_MEAN_VARIANCE"
PROBLEM_INSTANCE_ID = "INSTANCE_PORTFOLIO_MEAN_VARIANCE_FIXED_4"
LOW_GAMMA_SCENARIO_ID = "SCENARIO_PORTFOLIO_MEAN_VARIANCE_GAMMA_LOW"
HIGH_GAMMA_SCENARIO_ID = "SCENARIO_PORTFOLIO_MEAN_VARIANCE_GAMMA_HIGH"
LOW_GAMMA_TRACE_ID = "portfolio-mean-variance-gamma-low"
HIGH_GAMMA_TRACE_ID = "portfolio-mean-variance-gamma-high"

Policy = Literal["low", "high"]


def _text(ja: str, en: str) -> LocalizedText:
    return LocalizedText(ja=ja, en=en)


def _weights() -> list[tuple[float, ...]]:
    return [
        tuple(value / 20 for value in candidate)
        for candidate in product(range(13), repeat=4)
        if sum(candidate) == 20
    ]


def _diagnostics(
    weights: tuple[float, ...], gamma: float
) -> tuple[float, float, float, float, float]:
    parameters = get_runtime_problem(PROBLEM_INSTANCE_ID).instance.parameters
    mu = tuple(float(value) for value in cast(list[float], parameters["expected_returns"]))
    sigma = tuple(
        tuple(float(value) for value in row)
        for row in cast(list[list[float]], parameters["covariance"])
    )
    expected_return = sum(value * weight for value, weight in zip(mu, weights, strict=True))
    variance = sum(weights[i] * sigma[i][j] * weights[j] for i in range(4) for j in range(4))
    return (
        expected_return,
        variance,
        gamma * variance - expected_return,
        max(weights),
        abs(sum(weights) - 1.0),
    )


def _select(gamma: float) -> tuple[float, ...]:
    return min(_weights(), key=lambda weights: (_diagnostics(weights, gamma)[2], weights))


def _metric(metric_id: str, ja: str, en: str, value: float, unit: str) -> TraceMetric:
    return TraceMetric(
        metric_id=metric_id, label_ja=ja, label_en=en, value=round(value, 12), unit=unit
    )


def generate_portfolio_mean_variance_trace(
    *, dataset_version: str, policy: Policy
) -> AlgorithmTrace:
    gamma = 0.5 if policy == "low" else 4.0
    weights = _select(gamma)
    expected_return, variance, objective, max_weight, simplex_residual = _diagnostics(
        weights, gamma
    )
    scenario_id = LOW_GAMMA_SCENARIO_ID if policy == "low" else HIGH_GAMMA_SCENARIO_ID
    trace_id = LOW_GAMMA_TRACE_ID if policy == "low" else HIGH_GAMMA_TRACE_ID
    metrics = [
        _metric("expected_return", "期待収益", "expected return", expected_return, "return"),
        _metric("variance", "分散risk", "variance risk", variance, "variance"),
        _metric(
            "mean_variance_objective",
            "平均・分散objective",
            "mean-variance objective",
            objective,
            "objective",
        ),
        _metric(
            "maximum_weight", "最大配分比率", "maximum allocation weight", max_weight, "weight"
        ),
        _metric(
            "simplex_residual", "simplex残差", "simplex residual", simplex_residual, "residual"
        ),
    ]
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
            "definition": "gamma w^T Sigma w - mu^T w",
            "direction": "minimize",
            "risk_aversion": gamma,
        },
        preset={"preset_id": f"PORTFOLIO_MEAN_VARIANCE_GAMMA_{policy.upper()}"},
        parameters={
            "risk_aversion": gamma,
            "max_asset_weight": 0.6,
            "input_policy": "fixed_mean_and_covariance",
            "grid_step": 0.05,
        },
        initial_state={
            "point": [0.25, 0.25, 0.25, 0.25],
            "decision_domain": "four_asset_capped_simplex",
        },
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=1,
        stopping={"oracle_evaluations": 1},
        environment={"runtime": "deterministic_educational_grid", "version": GENERATOR_VERSION},
        fairness_statement="Both snapshots use the same four assets, expected returns, covariance, capped simplex, 0.05 teaching grid, and diagnostics; only risk aversion gamma changes.",
        frames=[
            TraceFrame(
                frame_index=0,
                iteration=0,
                oracle_evaluations=0,
                elapsed_steps=0,
                elapsed_time_ms=0.0,
                event_type="initialize",
                decision="not_applicable",
                explanation_key="fixed_inputs",
                event_label_ja="平均・共分散と制約を固定",
                event_label_en="Fix moments and constraints",
                keyframe=True,
                points=[],
                vectors=[],
                metrics=[],
                payload={"risk_aversion": gamma, "claim_scope": "fixed_moments_teaching_snapshot"},
            ),
            TraceFrame(
                frame_index=1,
                iteration=1,
                oracle_evaluations=1,
                elapsed_steps=1,
                elapsed_time_ms=100.0,
                event_type="allocation_snapshot",
                decision="accepted",
                explanation_key="allocation_diagnostics",
                event_label_ja="配分とdiagnosticを読む",
                event_label_en="Read allocation diagnostics",
                keyframe=True,
                points=[
                    TracePoint(
                        point_id="portfolio_weights",
                        role="decision",
                        coordinates=list(weights),
                        value=None,
                        label_ja="配分比率",
                        label_en="allocation weights",
                    )
                ],
                vectors=[],
                metrics=metrics,
                payload={
                    "weights": list(weights),
                    "risk_aversion": gamma,
                    "constraint_policy": "sum_to_one_and_0_to_0.6",
                },
            ),
        ],
        terminal_status="completed",
        terminal_summary_ja="固定した平均・共分散の下で、gammaだけを変えた配分snapshotを診断した。",
        terminal_summary_en="Diagnosed allocation snapshots after changing only gamma under fixed mean and covariance inputs.",
        source_ids=["S010", "S055"],
    )


def generate_portfolio_mean_variance_traces(*, dataset_version: str) -> list[AlgorithmTrace]:
    return [
        generate_portfolio_mean_variance_trace(dataset_version=dataset_version, policy="low"),
        generate_portfolio_mean_variance_trace(dataset_version=dataset_version, policy="high"),
    ]


def build_portfolio_mean_variance_scenario(trace: AlgorithmTrace) -> VisualizationScenario:
    high = trace.scenario_id == HIGH_GAMMA_SCENARIO_ID
    counterpart = LOW_GAMMA_SCENARIO_ID if high else HIGH_GAMMA_SCENARIO_ID
    observables = [
        VisualizationObservable(
            observable_id="expected_return", label_ja="期待収益", label_en="expected return"
        ),
        VisualizationObservable(
            observable_id="variance", label_ja="分散risk", label_en="variance risk"
        ),
        VisualizationObservable(
            observable_id="mean_variance_objective",
            label_ja="平均・分散objective",
            label_en="mean-variance objective",
        ),
        VisualizationObservable(
            observable_id="maximum_weight",
            label_ja="最大配分比率",
            label_en="maximum allocation weight",
        ),
        VisualizationObservable(
            observable_id="simplex_residual", label_ja="simplex残差", label_en="simplex residual"
        ),
    ]
    payload = canonical_trace_bytes(trace)
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=trace.dataset_version,
        scenario_id=trace.scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja="平均・分散配分: high gamma" if high else "平均・分散配分: low gamma",
        title_en="Mean-variance allocation: high gamma"
        if high
        else "Mean-variance allocation: low gamma",
        purpose="sensitivity",
        problem_definition_id=PROBLEM_DEFINITION_ID,
        problem_instance_id=PROBLEM_INSTANCE_ID,
        lesson=VisualizationLesson(
            learning_objective=_text(
                "期待収益・分散・可行性を同時に読み、gammaを手法順位へ読み替えない。",
                "Read return, variance, and feasibility together without turning gamma into a method ranking.",
            ),
            misconception=_text(
                "gammaを大きくすれば、将来損失も必ず小さくなる。",
                "A larger gamma necessarily lowers future losses.",
            ),
            expected_phenomenon_ja="固定入力でもgammaで配分・期待収益・分散が動く。",
            expected_phenomenon_en="Even with fixed inputs, gamma changes allocation, expected return, and variance.",
            success_signals=[
                VisualizationSignal(
                    signal_id="diagnostics_together",
                    label_ja="収益・分散・制約を同時に確認",
                    label_en="inspect return, variance, and constraints together",
                    observable_ids=[item.observable_id for item in observables],
                )
            ],
            failure_signals=[
                VisualizationSignal(
                    signal_id="future_guarantee",
                    label_ja="入力QPの解を将来保証と読む",
                    label_en="mistake the input-model solution for a future guarantee",
                    observable_ids=["expected_return", "variance"],
                )
            ],
            primary_observables=observables[:3],
            secondary_observables=observables[3:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="入力とgammaを固定",
                    title_en="Fix inputs and gamma",
                    observable_ids=["expected_return", "variance"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="目的値の内訳を読む",
                    title_en="Read the objective components",
                    observable_ids=["expected_return", "variance", "mean_variance_objective"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="gammaによる配分差を読む",
                    title_en="Read the allocation difference across gamma",
                    observable_ids=["expected_return", "variance", "maximum_weight"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="配分と可行性を照合",
                    title_en="Check allocation and feasibility",
                    observable_ids=["maximum_weight", "simplex_residual"],
                ),
            ],
            comparison_role="sensitivity_variant",
            prerequisite_concept_ids=["concept.simplex"],
            recommended_next_scenario_ids=[counterpart],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="将来returnの既知値は表示しない。",
                note_en="No future-return reference is shown.",
            ),
            static_summary=_text(
                "固定平均・共分散でgammaだけを変え、配分・期待収益・分散・制約残差を読む。",
                "Change only gamma with fixed moments, then read allocation, return, variance, and constraint residual.",
            ),
            text_alternative=_text(
                "各snapshotの資産比率、期待収益、分散、objective、最大比率、simplex残差を列挙する。",
                "List weights, expected return, variance, objective, maximum weight, and simplex residual for each snapshot.",
            ),
            derived_media_caption=_text(
                "名目平均・分散ポートフォリオのallocation ledger",
                "Nominal mean-variance portfolio allocation ledger",
            ),
            limitations_ja="固定4資産・固定推定値の教材であり、tail risk、推定誤差、将来performanceを示さない。",
            limitations_en="A fixed four-asset teaching ledger; it does not establish tail risk, estimation quality, or future performance.",
        ),
        guided_story=None,
        experiment=VisualizationExperiment(
            oracle_policy=["objective_value", "gradient", "constraint_value"],
            initial_condition=VisualizationInitialCondition(point=[0.25, 0.25, 0.25, 0.25]),
            parameter_preset_id=str(trace.preset["preset_id"]),
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=1),
            stopping={"oracle_evaluations": 1},
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
