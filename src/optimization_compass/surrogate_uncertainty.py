from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from optimization_compass.problem_registry import get_runtime_problem
from optimization_compass.visualization_scenarios import (
    GuidedStory,
    GuidedStoryStep,
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

Strategy = Literal["exploit", "explore"]
NoisePreset = Literal["noiseless", "small_noise"]
Fidelity = Literal["low", "high"]
EvaluationStatus = Literal["ok", "failed", "censored", "timeout"]
SURROGATE_GENERATOR_ID = "educational.surrogate_uncertainty.v1"
SURROGATE_GENERATOR_VERSION = "1.0.0"
CANONICAL_FLOAT_SIGNIFICANT_DIGITS = 8
CANONICAL_FLOAT_ZERO_TOLERANCE = 1e-9
_PROBLEM = get_runtime_problem("OBJECTIVE_EDUCATIONAL_WAVY_1D")


class RendererModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Observation(RendererModel):
    x: float
    value: float
    observed_value: float


class PredictivePoint(RendererModel):
    x: float
    true_value: float
    mean: float
    lower: float
    upper: float
    acquisition: float = Field(ge=0)


class SurrogateFrame(RendererModel):
    frame_index: int = Field(ge=0)
    oracle_evaluations: int = Field(gt=0)
    observations: list[Observation]
    predictive_summary: list[PredictivePoint]
    selected_point: float | None
    selected_mean: float | None
    selected_uncertainty: float | None
    selected_acquisition: float | None
    incumbent_x: float
    incumbent_value: float
    random_incumbent_value: float
    explanation_ja: str = Field(min_length=1)


class EvaluationLedgerEntry(RendererModel):
    call_id: int = Field(gt=0)
    x: float
    fidelity: Fidelity
    cost: float = Field(gt=0)
    status: EvaluationStatus
    observed_value: float | None
    accumulated_cost: float = Field(gt=0)
    accumulated_high_fidelity_equivalent_cost: float = Field(ge=0)
    best_so_far: float | None


class EvaluationLedger(RendererModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    fidelity_costs: dict[Fidelity, float]
    budget_cost: float = Field(gt=0)
    high_fidelity_equivalent_budget: float = Field(gt=0)
    calls: list[EvaluationLedgerEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_calls(self) -> Self:
        if set(self.fidelity_costs) != {"low", "high"}:
            raise ValueError("evaluation ledger must declare low and high fidelity costs")
        if any(cost <= 0 for cost in self.fidelity_costs.values()):
            raise ValueError("evaluation ledger fidelity costs must be positive")
        if [call.call_id for call in self.calls] != list(range(1, len(self.calls) + 1)):
            raise ValueError("evaluation ledger call IDs must be consecutive")
        accumulated = 0.0
        high_equivalent = 0.0
        best_high: float | None = None
        for call in self.calls:
            if call.cost != self.fidelity_costs[call.fidelity]:
                raise ValueError("evaluation ledger call cost must match its fidelity")
            accumulated += call.cost
            high_equivalent += call.cost / self.fidelity_costs["high"]
            if abs(call.accumulated_cost - accumulated) > 1e-9:
                raise ValueError("evaluation ledger accumulated cost is inconsistent")
            if abs(call.accumulated_high_fidelity_equivalent_cost - high_equivalent) > 1e-7:
                raise ValueError("evaluation ledger high-fidelity-equivalent cost is inconsistent")
            if call.status == "ok" and call.observed_value is None:
                raise ValueError("successful evaluation ledger calls require an observed value")
            if call.status != "ok" and call.observed_value is not None:
                raise ValueError(
                    "non-successful evaluation ledger calls must have null observed value"
                )
            if call.fidelity == "high" and call.status == "ok":
                if call.observed_value is None:
                    raise ValueError("successful high fidelity calls require an observed value")
                best_high = (
                    call.observed_value
                    if best_high is None
                    else min(best_high, call.observed_value)
                )
            if call.best_so_far != best_high:
                raise ValueError(
                    "evaluation ledger best-so-far must use successful high fidelity calls"
                )
        if accumulated > self.budget_cost + 1e-9:
            raise ValueError("evaluation ledger exceeds its cost budget")
        if (
            abs(
                self.high_fidelity_equivalent_budget
                - self.budget_cost / self.fidelity_costs["high"]
            )
            > 1e-7
        ):
            raise ValueError("evaluation ledger equivalent budget is inconsistent")
        return self


class SurrogateUncertaintyPayload(RendererModel):
    contract_version: Literal["1.0.0", "1.1.0"] = "1.0.0"
    strategy: Strategy
    noise_preset: NoisePreset
    noise_std: float = Field(ge=0)
    exploration_xi: float = Field(ge=0)
    domain: list[float] = Field(min_length=2, max_length=2)
    objective_expression: str = Field(min_length=1)
    truth_disclosure_ja: str = Field(min_length=1)
    frames: list[SurrogateFrame] = Field(min_length=1)
    random_history: list[Observation] = Field(min_length=1)
    evaluation_ledger: EvaluationLedger | None = None

    @model_validator(mode="after")
    def validate_frames(self) -> Self:
        if [frame.frame_index for frame in self.frames] != list(range(len(self.frames))):
            raise ValueError("frames must have consecutive frame_index values")
        final_budget = self.frames[-1].oracle_evaluations
        if len(self.random_history) != final_budget:
            raise ValueError("random comparison must use the same evaluation budget")
        if any(frame.oracle_evaluations != frame.frame_index + 3 for frame in self.frames):
            raise ValueError("frames must advance one oracle evaluation at a time")
        if self.contract_version == "1.1.0" and self.evaluation_ledger is None:
            raise ValueError("SurrogateUncertainty 1.1.0 requires an evaluation ledger")
        if self.contract_version == "1.0.0" and self.evaluation_ledger is not None:
            raise ValueError("SurrogateUncertainty 1.0.0 cannot include an evaluation ledger")
        return self


@dataclass(frozen=True)
class GeneratedSurrogateScenario:
    scenario: VisualizationScenario
    payload: SurrogateUncertaintyPayload
    payload_bytes: bytes


def canonical_renderer_bytes(model: RendererModel) -> bytes:
    serialized_payload: object = model.model_dump(mode="json")
    if isinstance(serialized_payload, dict):
        serialized_payload = {
            key: value for key, value in serialized_payload.items() if value is not None
        }
    payload = _canonicalize_floats(serialized_payload)
    value = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (value + "\n").encode()


def _canonicalize_floats(value: object) -> object:
    """Remove platform-specific libm noise before hashing renderer payloads."""
    if isinstance(value, float):
        if abs(value) < CANONICAL_FLOAT_ZERO_TOLERANCE:
            return 0.0
        normalized = float(format(value, f".{CANONICAL_FLOAT_SIGNIFICANT_DIGITS}g"))
        return 0.0 if normalized == 0.0 else normalized
    if isinstance(value, list):
        return [_canonicalize_floats(item) for item in value]
    if isinstance(value, dict):
        return {key: _canonicalize_floats(item) for key, item in value.items()}
    return value


def _truth(x: float) -> float:
    value = _PROBLEM.objective_value([x])
    if isinstance(value, tuple):
        raise ValueError("surrogate lesson requires a scalar objective")
    return value


def _solve_cholesky(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    lower = [[0.0] * size for _ in range(size)]
    for row in range(size):
        for col in range(row + 1):
            remainder = matrix[row][col] - sum(lower[row][k] * lower[col][k] for k in range(col))
            lower[row][col] = (
                math.sqrt(max(remainder, 1e-12)) if row == col else remainder / lower[col][col]
            )
    y: list[float] = []
    for row in range(size):
        y.append((vector[row] - sum(lower[row][k] * y[k] for k in range(row))) / lower[row][row])
    result = [0.0] * size
    for row in range(size - 1, -1, -1):
        result[row] = (
            y[row] - sum(lower[k][row] * result[k] for k in range(row + 1, size))
        ) / lower[row][row]
    return result


def _kernel(a: float, b: float, length_scale: float = 0.85) -> float:
    return math.exp(-0.5 * ((a - b) / length_scale) ** 2)


def _posterior(
    observations: list[Observation], grid: list[float], noise_std: float
) -> list[tuple[float, float]]:
    xs = [item.x for item in observations]
    ys = [item.observed_value for item in observations]
    mean_y = sum(ys) / len(ys)
    centered = [value - mean_y for value in ys]
    covariance = [
        [_kernel(a, b) + (noise_std**2 + 1e-6 if row == col else 0.0) for col, b in enumerate(xs)]
        for row, a in enumerate(xs)
    ]
    alpha = _solve_cholesky(covariance, centered)
    result: list[tuple[float, float]] = []
    for x in grid:
        k = [_kernel(x, observed_x) for observed_x in xs]
        mean = mean_y + sum(left * right for left, right in zip(k, alpha, strict=True))
        solved = _solve_cholesky(covariance, k)
        variance = max(
            1e-8,
            1.0 - sum(left * right for left, right in zip(k, solved, strict=True)),
        )
        result.append((mean, math.sqrt(variance)))
    return result


def _expected_improvement(mean: float, sigma: float, incumbent: float, xi: float) -> float:
    if sigma <= 1e-10:
        return 0.0
    improvement = incumbent - mean - xi
    z = improvement / sigma
    cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    density = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    return max(0.0, improvement * cdf + sigma * density)


def _build_payload(*, strategy: Strategy, noise_preset: NoisePreset) -> SurrogateUncertaintyPayload:
    seed = _PROBLEM.instance.seed_value
    if seed is None:
        raise ValueError("surrogate problem requires a fixed seed")
    bounds = _PROBLEM.instance.bounds.get("x")
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise ValueError("surrogate problem requires one-dimensional bounds")
    lower, upper = (float(bounds[0]), float(bounds[1]))
    noise_presets = _PROBLEM.instance.parameters.get("noise_presets")
    if not isinstance(noise_presets, dict):
        raise ValueError("surrogate problem requires noise presets")
    rng = random.Random(seed + (17 if noise_preset == "small_noise" else 0))
    noise_std = float(noise_presets[noise_preset])
    xi = 0.18 if strategy == "explore" else 0.0
    budget = 10
    initial = _PROBLEM.instance.initialization_candidates[0].get("point")
    if not isinstance(initial, list):
        raise ValueError("surrogate problem requires an initial design")
    initial_design = [float(value) for value in initial]
    grid = [round(lower + index * (upper - lower) / 80.0, 6) for index in range(81)]
    random_rng = random.Random(seed)
    random_noise_rng = random.Random(seed + 991 + (17 if noise_preset == "small_noise" else 0))
    random_xs = [
        *initial_design,
        *[random_rng.uniform(lower, upper) for _ in range(budget - len(initial_design))],
    ]
    random_history = [
        Observation(
            x=x,
            value=_truth(x),
            observed_value=_truth(x)
            + (random_noise_rng.gauss(0.0, noise_std) if noise_std else 0.0),
        )
        for x in random_xs
    ]

    def observe(x: float) -> Observation:
        truth = _truth(x)
        measured = truth + (rng.gauss(0.0, noise_std) if noise_std else 0.0)
        return Observation(x=x, value=truth, observed_value=measured)

    observations = [observe(x) for x in initial_design]
    frames: list[SurrogateFrame] = []
    while True:
        posterior = _posterior(observations, grid, noise_std)
        incumbent = min(observations, key=lambda item: item.observed_value)
        observed_xs = {round(item.x, 6) for item in observations}
        points = [
            PredictivePoint(
                x=x,
                true_value=_truth(x),
                mean=mean,
                lower=mean - 1.96 * sigma,
                upper=mean + 1.96 * sigma,
                acquisition=(
                    0.0
                    if round(x, 6) in observed_xs
                    else _expected_improvement(mean, sigma, incumbent.observed_value, xi)
                ),
            )
            for x, (mean, sigma) in zip(grid, posterior, strict=True)
        ]
        selected = (
            max(points, key=lambda item: (item.acquisition, -abs(item.x)))
            if len(observations) < budget
            else None
        )
        explanation = (
            f"期待改善量 EI={selected.acquisition:.3f} が最大の x={selected.x:.2f} を次に選択。"
            f"予測平均 {selected.mean:.3f} と不確実性幅 "
            f"{selected.upper - selected.mean:.3f} の両方が選択理由です。"
            if selected
            else "評価予算を使い切りました。観測済みの最良値を最終 incumbent とします。"
        )
        frames.append(
            SurrogateFrame(
                frame_index=len(frames),
                oracle_evaluations=len(observations),
                observations=list(observations),
                predictive_summary=points,
                selected_point=selected.x if selected else None,
                selected_mean=selected.mean if selected else None,
                selected_uncertainty=(selected.upper - selected.mean) if selected else None,
                selected_acquisition=selected.acquisition if selected else None,
                incumbent_x=incumbent.x,
                incumbent_value=incumbent.observed_value,
                random_incumbent_value=min(
                    item.observed_value for item in random_history[: len(observations)]
                ),
                explanation_ja=explanation,
            )
        )
        if selected is None:
            break
        observations.append(observe(selected.x))

    return SurrogateUncertaintyPayload(
        strategy=strategy,
        noise_preset=noise_preset,
        noise_std=noise_std,
        exploration_xi=xi,
        domain=[lower, upper],
        objective_expression=str(_PROBLEM.instance.display["expression"]),
        truth_disclosure_ja=(
            "破線の真の目的関数は教材用の答え合わせです。"
            "optimizerは観測点以外の真値を参照しません。"
        ),
        frames=frames,
        random_history=random_history,
    )


def generate_surrogate_scenario(
    *, dataset_version: str, strategy: Strategy, noise_preset: NoisePreset
) -> GeneratedSurrogateScenario:
    seed_value = _PROBLEM.instance.seed_value
    if seed_value is None:
        raise ValueError("surrogate problem requires a fixed seed")
    payload = _build_payload(strategy=strategy, noise_preset=noise_preset)
    payload_bytes = canonical_renderer_bytes(payload)
    stem = f"bo-{strategy}-{noise_preset}"
    scenario_id = f"SCENARIO_BO_1D_{strategy.upper()}_{noise_preset.upper()}"
    budget = payload.frames[-1].oracle_evaluations
    initial_design = [item.x for item in payload.frames[0].observations]
    variant = strategy != "explore" or noise_preset != "noiseless"
    guided_story = (
        None
        if variant
        else GuidedStory(
            story_version="1.0.0",
            introduction=LocalizedText(
                ja="初期観測から次点選択、予算到達までを4つのcueで追います。",
                en="Follow four cues from initial observations to the evaluation budget.",
            ),
            steps=[
                GuidedStoryStep(
                    milestone_id="start",
                    annotation=LocalizedText(
                        ja="最初に観測済みの点と、その間に残る不確実性を見ます。",
                        en="Start with observed points and uncertainty between them.",
                    ),
                    frame_index=0,
                    auto_pause=True,
                    focus_target="observations",
                    viewport_preset="overview",
                    camera_preset=None,
                    playback_speed=1.0,
                    visible_layers=["observations", "posterior_mean", "posterior_uncertainty"],
                ),
                GuidedStoryStep(
                    milestone_id="first_change",
                    annotation=LocalizedText(
                        ja="Expected Improvementの山から次の評価点が選ばれます。",
                        en="The next evaluation is selected from an Expected Improvement peak.",
                    ),
                    frame_index=min(1, len(payload.frames) - 1),
                    auto_pause=True,
                    focus_target="selected_candidate",
                    viewport_preset="acquisition",
                    camera_preset=None,
                    playback_speed=0.5,
                    visible_layers=[
                        "observations",
                        "posterior_mean",
                        "posterior_uncertainty",
                        "expected_improvement",
                        "selected_candidate",
                    ],
                ),
                GuidedStoryStep(
                    milestone_id="pattern_visible",
                    annotation=LocalizedText(
                        ja="観測を追加した近傍で不確実性が縮むことを確認します。",
                        en="Uncertainty contracts near the newly added observation.",
                    ),
                    frame_index=min(3, len(payload.frames) - 1),
                    auto_pause=True,
                    focus_target="posterior_uncertainty",
                    viewport_preset="uncertainty",
                    camera_preset=None,
                    playback_speed=1.0,
                    visible_layers=["observations", "posterior_mean", "posterior_uncertainty"],
                ),
                GuidedStoryStep(
                    milestone_id="termination",
                    annotation=LocalizedText(
                        ja="固定評価予算で得たincumbentを確認し、一般的優越性とは分けます。",
                        en="Inspect the incumbent under the fixed budget without claiming "
                        "general superiority.",
                    ),
                    frame_index=len(payload.frames) - 1,
                    auto_pause=True,
                    focus_target="incumbent_history",
                    viewport_preset="terminal",
                    camera_preset=None,
                    playback_speed=0.5,
                    visible_layers=["observations", "posterior_mean", "incumbent_history"],
                ),
            ],
            summary=LocalizedText(
                ja="BOは観測でsurrogateを更新し、acquisitionで次の高価な評価を選びます。",
                en="BO updates a surrogate from observations and uses acquisition to choose "
                "the next expensive evaluation.",
            ),
        )
    )
    scenario = VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=dataset_version,
        scenario_id=scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja=f"高価な1次元black-box: {strategy} / {noise_preset}",
        title_en=f"Expensive 1D black box: {strategy} / {noise_preset}",
        purpose="sensitivity" if variant else "mechanism",
        problem_definition_id="PROBLEM_EXPENSIVE_BLACK_BOX_1D",
        problem_instance_id="OBJECTIVE_EDUCATIONAL_WAVY_1D",
        lesson=VisualizationLesson(
            learning_objective=LocalizedText(
                ja="観測からsurrogateとacquisitionを更新して次の評価点を選ぶ流れを読む",
                en="Read how observations update the surrogate and acquisition to select "
                "the next point",
            ),
            misconception=(
                LocalizedText(
                    ja="探索係数や観測noiseを変えても次の評価点と不確実性は同じになる",
                    en="Changing exploration weight or observation noise leaves the next "
                    "point and uncertainty unchanged",
                )
                if variant
                else None
            ),
            expected_phenomenon_ja=(
                "観測からsurrogateとExpected Improvementを更新し、次の評価点を選ぶ"
                if not variant
                else "探索係数または観測noiseの違いで次点と不確実性表示が変わる"
            ),
            expected_phenomenon_en=(
                "Update the surrogate and Expected Improvement from observations "
                "to choose the next evaluation"
                if not variant
                else "Exploration weight or observation noise changes the selected point "
                "and uncertainty"
            ),
            success_signals=[
                VisualizationSignal(
                    signal_id="candidate_selected_from_acquisition",
                    label_ja="acquisitionの山から次の評価点が選ばれる",
                    label_en="The next evaluation is selected from an acquisition peak",
                    observable_ids=[
                        "expected_improvement",
                        "selected_candidate",
                        "posterior_uncertainty",
                    ],
                )
            ],
            failure_signals=(
                [
                    VisualizationSignal(
                        signal_id="variant_changes_decision",
                        label_ja="baselineと異なる候補点または不確実性になる",
                        label_en="Candidate or uncertainty differs from the baseline",
                        observable_ids=[
                            "posterior_uncertainty",
                            "expected_improvement",
                            "selected_candidate",
                        ],
                    )
                ]
                if variant
                else []
            ),
            primary_observables=[
                VisualizationObservable(
                    observable_id="observations", label_ja="観測点", label_en="observations"
                ),
                VisualizationObservable(
                    observable_id="posterior_mean",
                    label_ja="surrogate平均",
                    label_en="posterior mean",
                ),
                VisualizationObservable(
                    observable_id="posterior_uncertainty",
                    label_ja="予測不確実性",
                    label_en="posterior uncertainty",
                ),
                VisualizationObservable(
                    observable_id="expected_improvement",
                    label_ja="Expected Improvement",
                    label_en="Expected Improvement",
                ),
                VisualizationObservable(
                    observable_id="selected_candidate",
                    label_ja="次候補",
                    label_en="selected candidate",
                ),
            ],
            secondary_observables=[
                VisualizationObservable(
                    observable_id="incumbent_history",
                    label_ja="best-so-far履歴",
                    label_en="incumbent history",
                )
            ],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="初期観測を確認",
                    title_en="Inspect the initial observations",
                    observable_ids=["observations"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="最初のsurrogate更新と次点選択",
                    title_en="First surrogate update and candidate selection",
                    observable_ids=[
                        "posterior_mean",
                        "posterior_uncertainty",
                        "expected_improvement",
                        "selected_candidate",
                    ],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="観測追加で不確実性が変わる",
                    title_en="Uncertainty changes as observations are added",
                    observable_ids=["observations", "posterior_uncertainty"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="評価予算到達時のincumbentを確認",
                    title_en="Inspect the incumbent at the evaluation budget",
                    observable_ids=["incumbent_history"],
                ),
            ],
            comparison_role="sensitivity_variant" if variant else "primary_example",
            prerequisite_concept_ids=[
                "CONCEPT_SURROGATE_MODEL",
                "CONCEPT_ACQUISITION_FUNCTION",
            ],
            recommended_next_scenario_ids=[
                "SCENARIO_BO_1D_EXPLORE_NOISELESS"
                if variant
                else "SCENARIO_BO_1D_EXPLOIT_NOISELESS"
            ],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="optimizerが参照しない真の目的関数は教材用overlayとしてのみ表示する",
                note_en="Show the optimizer-hidden true objective only as an educational overlay",
            ),
            static_summary=LocalizedText(
                ja="観測、surrogate平均、不確実性、Expected Improvement、次候補を同じframeで示す。",
                en="Show observations, surrogate mean, uncertainty, Expected Improvement, "
                "and next candidate in one frame.",
            ),
            text_alternative=LocalizedText(
                ja="各評価で観測点、incumbent、次候補、acquisition、不確実性を読み上げる。",
                en="At each evaluation, report observations, incumbent, next candidate, "
                "acquisition, and uncertainty.",
            ),
            derived_media_caption=LocalizedText(
                ja=f"Bayesian Optimization: {strategy} / {noise_preset}でのsurrogate更新",
                en=f"Bayesian Optimization: surrogate updates for {strategy} / {noise_preset}",
            ),
            limitations_ja=(
                "固定seed・1次元・RBF kernelの教育用run。kernel/noise仮定、高次元化、"
                "有限予算では挙動が変わり、大域最適性を証明しない"
            ),
            limitations_en=(
                "A fixed-seed one-dimensional educational run with an RBF kernel; "
                "kernel and noise assumptions, higher dimensions, and finite budgets "
                "change behavior and do not prove global optimality"
            ),
        ),
        guided_story=guided_story,
        experiment=VisualizationExperiment(
            oracle_policy=["objective_value"],
            initial_condition=VisualizationInitialCondition(point=initial_design),
            parameter_preset_id=f"BO_{strategy.upper()}_{noise_preset.upper()}",
            seed=VisualizationSeed(status="fixed", value=seed_value),
            budget=VisualizationBudget(metric="oracle_evaluations", value=budget),
            stopping={"max_oracle_evaluations": budget},
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id=f"RUN_BO_{strategy.upper()}_{noise_preset.upper()}_{seed_value}",
                method_id="M_BAYESIAN_OPT_GP",
                profile_id="PROFILE_BAYESIAN_OPT_GP_1D",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=f"ARTIFACT_{stem.upper().replace('-', '_')}",
            ),
            VisualizationRun(
                run_id=f"RUN_RANDOM_{strategy.upper()}_{noise_preset.upper()}_{seed_value}",
                method_id="M_RANDOM_SEARCH",
                profile_id="PROFILE_RANDOM_SEARCH_1D",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=f"ARTIFACT_{stem.upper().replace('-', '_')}_RANDOM_BASELINE",
            ),
        ],
        artifact=VisualizationArtifact(
            artifact_kind="executable_trace",
            artifact_contract="SurrogateUncertainty",
            artifact_contract_version="1.0.0",
            renderer_family="surrogate_uncertainty",
            renderer_contract_version="1.0.0",
            observable_ids=[
                "observations",
                "posterior_mean",
                "posterior_uncertainty",
                "expected_improvement",
                "selected_candidate",
                "incumbent_history",
            ],
            payload_path=f"visualizations/{stem}.json",
            payload_bytes=len(payload_bytes),
            payload_sha256=sha256(payload_bytes).hexdigest(),
        ),
        source_ids=["S035", "S059", "S075"],
        last_verified="2026-07-15",
    )
    return GeneratedSurrogateScenario(
        scenario=scenario,
        payload=payload,
        payload_bytes=payload_bytes,
    )


def _multi_fidelity_observation(
    x: float, fidelity: Fidelity
) -> tuple[EvaluationStatus, float | None]:
    if fidelity == "low" and x < -2.8:
        return "timeout", None
    if fidelity == "low" and x > 2.4:
        return "failed", None
    if fidelity == "high" and x < -2.2:
        return "censored", None
    high = _truth(x)
    bias = 0.18 * math.sin(1.4 * x + 0.3) if fidelity == "low" else 0.0
    deterministic_noise = (
        0.03 * math.sin(7.0 * x) if fidelity == "low" else 0.01 * math.sin(7.0 * x)
    )
    return "ok", high + bias + deterministic_noise


def _generate_evaluation_ledger_payload(
    call_plan: list[tuple[float, Fidelity]],
) -> tuple[SurrogateUncertaintyPayload, bytes]:
    """Generate one deterministic ledger payload under the shared simulator policy."""
    fidelity_costs: dict[Fidelity, float] = {"low": 1.0, "high": 12.0}
    if len(call_plan) < 3:
        raise ValueError("evaluation ledger scenarios require at least three calls")
    grid = [round(-3.0 + index * 6.0 / 80.0, 6) for index in range(81)]
    observations: list[Observation] = []
    ledger: list[EvaluationLedgerEntry] = []
    frames: list[SurrogateFrame] = []
    accumulated_cost = 0.0
    accumulated_high_equivalent = 0.0
    best_high: float | None = None
    for index, (x, fidelity) in enumerate(call_plan):
        status, observed_value = _multi_fidelity_observation(x, fidelity)
        cost = fidelity_costs[fidelity]
        accumulated_cost += cost
        accumulated_high_equivalent += cost / fidelity_costs["high"]
        if fidelity == "high" and status == "ok":
            if observed_value is None:
                raise ValueError("successful high fidelity calls require an observed value")
            best_high = observed_value if best_high is None else min(best_high, observed_value)
        ledger.append(
            EvaluationLedgerEntry(
                call_id=index + 1,
                x=x,
                fidelity=fidelity,
                cost=cost,
                status=status,
                observed_value=observed_value,
                accumulated_cost=accumulated_cost,
                accumulated_high_fidelity_equivalent_cost=accumulated_high_equivalent,
                best_so_far=best_high,
            )
        )
        if status == "ok":
            if observed_value is None:
                raise ValueError("successful calls require an observed value")
            observations.append(Observation(x=x, value=_truth(x), observed_value=observed_value))
        if index < 2:
            continue
        posterior = _posterior(observations, grid, 0.0)
        incumbent = min(observations, key=lambda item: item.observed_value)
        observed_xs = {round(item.x, 6) for item in observations}
        points = [
            PredictivePoint(
                x=grid_x,
                true_value=_truth(grid_x),
                mean=mean,
                lower=mean - 1.96 * sigma,
                upper=mean + 1.96 * sigma,
                acquisition=(
                    0.0
                    if round(grid_x, 6) in observed_xs
                    else _expected_improvement(mean, sigma, incumbent.observed_value, 0.18)
                ),
            )
            for grid_x, (mean, sigma) in zip(grid, posterior, strict=True)
        ]
        next_call = call_plan[index + 1] if index + 1 < len(call_plan) else None
        selected = None
        if next_call is not None:
            selected = next(
                (point for point in points if abs(point.x - next_call[0]) < 1e-5),
                None,
            )
        if selected and next_call is not None:
            explanation = (
                f"次のledger callは {next_call[1]} fidelity の x={next_call[0]:.2f}。"
                f" surrogate上のEIは {selected.acquisition:.3f} ですが、"
                "この固定教材はfidelity policyとstatus記録を読むためのrunです。"
            )
        else:
            explanation = "ledgerの予算を使い切りました。high fidelityのbest-so-farを確認します。"
        frames.append(
            SurrogateFrame(
                frame_index=len(frames),
                oracle_evaluations=index + 1,
                observations=list(observations),
                predictive_summary=points,
                selected_point=selected.x if selected else None,
                selected_mean=selected.mean if selected else None,
                selected_uncertainty=(selected.upper - selected.mean) if selected else None,
                selected_acquisition=selected.acquisition if selected else None,
                incumbent_x=incumbent.x,
                incumbent_value=incumbent.observed_value,
                random_incumbent_value=min(_truth(item[0]) for item in call_plan[: index + 1]),
                explanation_ja=explanation,
            )
        )
    random_history = [
        Observation(x=x, value=_truth(x), observed_value=_truth(x)) for x, _ in call_plan
    ]
    payload = SurrogateUncertaintyPayload(
        contract_version="1.1.0",
        strategy="explore",
        noise_preset="noiseless",
        noise_std=0.0,
        exploration_xi=0.18,
        domain=[-3.0, 3.0],
        objective_expression=str(_PROBLEM.instance.display["expression"]),
        truth_disclosure_ja=(
            "破線の真のhigh fidelity目的関数は教材用の答え合わせです。"
            "ledgerの失敗・censored・timeoutは目的値へ置換していません。"
        ),
        frames=frames,
        random_history=random_history,
        evaluation_ledger=EvaluationLedger(
            fidelity_costs=fidelity_costs,
            budget_cost=36.0,
            high_fidelity_equivalent_budget=3.0,
            calls=ledger,
        ),
    )
    payload_bytes = canonical_renderer_bytes(payload)
    return payload, payload_bytes


def generate_evaluation_ledger_scenario(*, dataset_version: str) -> GeneratedSurrogateScenario:
    """Generate the bounded multi-fidelity teaching run for the Gallery case."""
    call_plan: list[tuple[float, Fidelity]] = [
        (-2.9, "low"),
        (-2.6, "low"),
        (0.0, "low"),
        (2.6, "low"),
        (1.1, "low"),
        (0.6, "low"),
        (2.2, "low"),
        (-1.5, "low"),
        (0.3, "low"),
        (1.4, "low"),
        (2.45, "low"),
        (-0.4, "low"),
        (-2.4, "high"),
        (1.7, "high"),
    ]
    payload, payload_bytes = _generate_evaluation_ledger_payload(call_plan)
    scenario_id = "SCENARIO_BO_1D_MULTIFIDELITY_LEDGER"
    initial_design = [item[0] for item in call_plan[:3]]
    scenario = VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=dataset_version,
        scenario_id=scenario_id,
        identity_status="generated_only",
        canonical_scenario_id=None,
        title_ja="低／高 fidelity simulator の評価ledger",
        title_en="Evaluation ledger for a low/high-fidelity simulator",
        purpose="mechanism",
        problem_definition_id="PROBLEM_EXPENSIVE_BLACK_BOX_1D",
        problem_instance_id="OBJECTIVE_EDUCATIONAL_WAVY_1D",
        lesson=VisualizationLesson(
            learning_objective=LocalizedText(
                ja=(
                    "simulator callごとのfidelity・cost・statusを追い、"
                    "high fidelityのbest-so-farを読む"
                ),
                en=(
                    "Track fidelity, cost, and status for each simulator call and read "
                    "the high-fidelity best-so-far"
                ),
            ),
            misconception=LocalizedText(
                ja="low fidelityの回数や失敗をhigh fidelityの成功評価と同じものとして数える",
                en=(
                    "Treat low-fidelity calls and failed calls as equivalent to "
                    "successful high-fidelity evaluations"
                ),
            ),
            expected_phenomenon_ja=(
                "安いlow fidelityを重ねても、累積costとhigh fidelityのbest-so-farは別の軸で進む"
            ),
            expected_phenomenon_en=(
                "Cheap low-fidelity calls advance separately from accumulated cost and "
                "the high-fidelity best-so-far"
            ),
            success_signals=[
                VisualizationSignal(
                    signal_id="ledger_preserves_fidelity_cost_status",
                    label_ja="callごとのfidelity・cost・statusが残る",
                    label_en="Each call preserves fidelity, cost, and status",
                    observable_ids=[
                        "evaluation_ledger",
                        "fidelity",
                        "call_cost",
                        "evaluation_status",
                    ],
                ),
                VisualizationSignal(
                    signal_id="ledger_separates_high_fidelity_best",
                    label_ja="high fidelity成功だけでbest-so-farを更新する",
                    label_en="Only successful high-fidelity calls update best-so-far",
                    observable_ids=["accumulated_budget", "best_so_far"],
                ),
            ],
            failure_signals=[
                VisualizationSignal(
                    signal_id="ledger_does_not_replace_failure_with_objective",
                    label_ja="failed・censored・timeoutを目的値に置換しない",
                    label_en=(
                        "Failed, censored, and timeout calls are not replaced by objective values"
                    ),
                    observable_ids=["evaluation_ledger", "evaluation_status"],
                )
            ],
            primary_observables=[
                VisualizationObservable(
                    observable_id="evaluation_ledger",
                    label_ja="評価ledger",
                    label_en="evaluation ledger",
                ),
                VisualizationObservable(
                    observable_id="fidelity", label_ja="fidelity", label_en="fidelity"
                ),
                VisualizationObservable(
                    observable_id="call_cost", label_ja="call cost", label_en="call cost"
                ),
                VisualizationObservable(
                    observable_id="evaluation_status",
                    label_ja="評価status",
                    label_en="evaluation status",
                ),
                VisualizationObservable(
                    observable_id="accumulated_budget",
                    label_ja="累積budget",
                    label_en="accumulated budget",
                ),
                VisualizationObservable(
                    observable_id="best_so_far",
                    label_ja="high fidelity best-so-far",
                    label_en="high-fidelity best-so-far",
                ),
            ],
            secondary_observables=[
                VisualizationObservable(
                    observable_id="posterior_uncertainty",
                    label_ja="surrogate不確実性",
                    label_en="surrogate uncertainty",
                )
            ],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="最初のcallとfidelityを見る",
                    title_en="Inspect the first calls and fidelity",
                    observable_ids=["evaluation_ledger", "fidelity"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="low fidelityのcostを累積する",
                    title_en="Accumulate low-fidelity cost",
                    observable_ids=["call_cost", "accumulated_budget"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="失敗statusを値と分ける",
                    title_en="Separate failure status from values",
                    observable_ids=["evaluation_status", "best_so_far"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="予算内のhigh fidelity結果を確認する",
                    title_en="Inspect high-fidelity results within budget",
                    observable_ids=["accumulated_budget", "best_so_far"],
                ),
            ],
            comparison_role="primary_example",
            prerequisite_concept_ids=["CONCEPT_SURROGATE_MODEL", "CONCEPT_EVALUATION_COST"],
            recommended_next_scenario_ids=["SCENARIO_BO_1D_EXPLORE_NOISELESS"],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="連続問題の最適性やfidelity補正の妥当性はこの固定runから判定しない",
                note_en=(
                    "This fixed run does not establish continuous optimality or validate "
                    "a fidelity correction model"
                ),
            ),
            static_summary=LocalizedText(
                ja=(
                    "低／高 fidelity、call cost、累積budget、failed・censored・timeout、"
                    "high fidelity best-so-farを同じledgerで示す。"
                ),
                en=(
                    "Show low/high fidelity, call cost, accumulated budget, "
                    "failed/censored/timeout status, and high-fidelity best-so-far in one ledger."
                ),
            ),
            text_alternative=LocalizedText(
                ja=(
                    "callを順に読み、fidelity、cost、status、累積budget、"
                    "high fidelity best-so-farを表で確認する。Compareの勝敗は表示しない。"
                ),
                en=(
                    "Read calls in order and inspect fidelity, cost, status, accumulated "
                    "budget, and high-fidelity best-so-far in the table; no Compare winner "
                    "is shown."
                ),
            ),
            derived_media_caption=LocalizedText(
                ja="低／高 fidelity simulatorのevaluation ledger",
                en="Evaluation ledger for a low/high-fidelity simulator",
            ),
            limitations_ja=(
                "固定seed・1次元・決定論的な教育用policy。fidelity間のsurrogate補正、"
                "parallel/asynchronous実行、実runtime、retry、物理simulatorのfailure原因は扱わず、"
                "この固定run単独からfidelity policyやmethodの優劣を主張しない。"
            ),
            limitations_en=(
                "A fixed-seed one-dimensional educational policy. It does not model "
                "cross-fidelity surrogate correction, parallel/asynchronous execution, "
                "real runtime, retries, or physical simulator failure causes, and this fixed "
                "run alone does not establish a fidelity-policy or method ranking."
            ),
        ),
        experiment=VisualizationExperiment(
            oracle_policy=["objective_value"],
            initial_condition=VisualizationInitialCondition(point=initial_design),
            parameter_preset_id=scenario_id.removeprefix("SCENARIO_"),
            seed=VisualizationSeed(status="fixed", value=2604),
            budget=VisualizationBudget(metric="oracle_evaluations", value=len(call_plan)),
            stopping={"max_oracle_evaluations": len(call_plan), "max_total_cost": 36},
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id="RUN_BO_MULTIFIDELITY_LEDGER_2604",
                method_id="M_BAYESIAN_OPT_GP",
                profile_id="PROFILE_BAYESIAN_OPT_GP_1D",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id="ARTIFACT_BO_MULTIFIDELITY_LEDGER",
            )
        ],
        artifact=VisualizationArtifact(
            artifact_kind="executable_trace",
            artifact_contract="SurrogateUncertainty",
            artifact_contract_version="1.1.0",
            renderer_family="surrogate_uncertainty",
            renderer_contract_version="1.1.0",
            observable_ids=[
                "evaluation_ledger",
                "fidelity",
                "call_cost",
                "evaluation_status",
                "accumulated_budget",
                "best_so_far",
                "posterior_uncertainty",
            ],
            payload_path="visualizations/bo-multi-fidelity-ledger.json",
            payload_bytes=len(payload_bytes),
            payload_sha256=sha256(payload_bytes).hexdigest(),
        ),
        source_ids=["S035", "S038", "S059", "S069", "S075"],
        last_verified="2026-07-19",
    )
    return GeneratedSurrogateScenario(
        scenario=scenario, payload=payload, payload_bytes=payload_bytes
    )


def _evaluation_ledger_variant(
    *,
    dataset_version: str,
    call_plan: list[tuple[float, Fidelity]],
    scenario_id: str,
    artifact_id: str,
    payload_path: str,
    title_ja: str,
    title_en: str,
    purpose: Literal["mechanism", "failure_contrast"],
    comparison_role: Literal["baseline", "failure_contrast"],
    learning_objective_ja: str,
    learning_objective_en: str,
    misconception_ja: str,
    misconception_en: str,
    expected_phenomenon_ja: str,
    expected_phenomenon_en: str,
    summary_ja: str,
    summary_en: str,
    limitations_ja: str,
    limitations_en: str,
) -> GeneratedSurrogateScenario:
    base = generate_evaluation_ledger_scenario(dataset_version=dataset_version)
    payload, payload_bytes = _generate_evaluation_ledger_payload(call_plan)
    lesson = base.scenario.lesson.model_copy(
        update={
            "learning_objective": LocalizedText(ja=learning_objective_ja, en=learning_objective_en),
            "misconception": LocalizedText(ja=misconception_ja, en=misconception_en),
            "expected_phenomenon_ja": expected_phenomenon_ja,
            "expected_phenomenon_en": expected_phenomenon_en,
            "comparison_role": comparison_role,
            "static_summary": LocalizedText(ja=summary_ja, en=summary_en),
            "text_alternative": LocalizedText(ja=summary_ja, en=summary_en),
            "derived_media_caption": LocalizedText(ja=title_ja, en=title_en),
            "limitations_ja": limitations_ja,
            "limitations_en": limitations_en,
        }
    )
    scenario = base.scenario.model_copy(
        update={
            "scenario_id": scenario_id,
            "title_ja": title_ja,
            "title_en": title_en,
            "purpose": purpose,
            "lesson": lesson,
            "experiment": base.scenario.experiment.model_copy(
                update={
                    "initial_condition": VisualizationInitialCondition(
                        point=[item[0] for item in call_plan[:3]]
                    ),
                    "parameter_preset_id": scenario_id.removeprefix("SCENARIO_"),
                    "budget": VisualizationBudget(
                        metric="oracle_evaluations", value=len(call_plan)
                    ),
                    "stopping": {
                        "max_oracle_evaluations": len(call_plan),
                        "max_total_cost": 36,
                    },
                }
            ),
            "runs": [
                base.scenario.runs[0].model_copy(
                    update={
                        "run_id": f"RUN_{scenario_id.removeprefix('SCENARIO_')}_2604",
                        "artifact_id": artifact_id,
                    }
                )
            ],
            "artifact": base.scenario.artifact.model_copy(
                update={
                    "payload_path": payload_path,
                    "payload_bytes": len(payload_bytes),
                    "payload_sha256": sha256(payload_bytes).hexdigest(),
                }
            ),
        }
    )
    scenario = VisualizationScenario.model_validate(scenario.model_dump(mode="json"))
    return GeneratedSurrogateScenario(
        scenario=scenario, payload=payload, payload_bytes=payload_bytes
    )


def generate_high_fidelity_baseline_scenario(*, dataset_version: str) -> GeneratedSurrogateScenario:
    """Generate the cost-aligned high-fidelity-only Compare member."""
    return _evaluation_ledger_variant(
        dataset_version=dataset_version,
        call_plan=[(-2.9, "high"), (-2.6, "high"), (0.0, "high")],
        scenario_id="SCENARIO_BO_1D_HIGH_FIDELITY_BASELINE",
        artifact_id="ARTIFACT_BO_HIGH_FIDELITY_BASELINE",
        payload_path="visualizations/bo-high-fidelity-baseline.json",
        title_ja="high fidelityだけで使う同一cost budget",
        title_en="Same cost budget spent on high fidelity only",
        purpose="mechanism",
        comparison_role="baseline",
        learning_objective_ja=(
            "同じ初期designとcost budgetでhigh fidelityだけを選ぶ場合のledgerを読む"
        ),
        learning_objective_en=(
            "Read a high-fidelity-only ledger under the same initial design and cost budget"
        ),
        misconception_ja=(
            "3回のhigh fidelity callと14回のmixed-fidelity callをiteration数だけで比較する"
        ),
        misconception_en=(
            "Compare three high-fidelity calls with fourteen mixed-fidelity calls by "
            "iteration count alone"
        ),
        expected_phenomenon_ja=(
            "同じ36 costでもfidelity配分によりcall数と成功・censoredの内訳が変わる"
        ),
        expected_phenomenon_en=(
            "The same cost of 36 yields different call and status counts when fidelity "
            "allocation changes"
        ),
        summary_ja=(
            "固定した3点をhigh fidelityだけで評価し、"
            "36 costと3 high-fidelity-equivalentを使い切る。"
        ),
        summary_en=(
            "Evaluate the same three fixed points only at high fidelity, consuming cost 36 "
            "and three high-fidelity equivalents."
        ),
        limitations_ja=(
            "固定3点の教育用baselineであり、"
            "high-fidelity-only policyやmethodの一般的性能を示さない。"
        ),
        limitations_en=(
            "A fixed three-point teaching baseline; it does not establish general "
            "performance of a high-fidelity-only policy or method."
        ),
    )


def generate_low_fidelity_bias_scenario(*, dataset_version: str) -> GeneratedSurrogateScenario:
    """Generate the independent Theater failure lesson for fidelity discrepancy."""
    generated = _evaluation_ledger_variant(
        dataset_version=dataset_version,
        call_plan=[(-1.1, "low"), (0.5, "low"), (-1.1, "high"), (0.5, "high")],
        scenario_id="SCENARIO_BO_1D_LOW_FIDELITY_BIAS",
        artifact_id="ARTIFACT_BO_LOW_FIDELITY_BIAS",
        payload_path="visualizations/bo-low-fidelity-bias.json",
        title_ja="low-fidelity biasで候補順位が反転する",
        title_en="Low-fidelity bias reverses candidate ordering",
        purpose="failure_contrast",
        comparison_role="failure_contrast",
        learning_objective_ja=(
            "同じ2点のlow/high観測を照合し、fidelity discrepancyによる順位反転を検出する"
        ),
        learning_objective_en=(
            "Match low/high observations at two points and detect an ordering reversal "
            "caused by fidelity discrepancy"
        ),
        misconception_ja="low fidelityで良い候補はhigh fidelityでも必ず良いとみなす",
        misconception_en=(
            "Assume a candidate ranked well at low fidelity must also rank well at high fidelity"
        ),
        expected_phenomenon_ja=(
            "low fidelityではx=-1.1が良く見えるが、high fidelityではx=0.5の方が良い"
        ),
        expected_phenomenon_en="Low fidelity favors x=-1.1, while high fidelity favors x=0.5",
        summary_ja=(
            "2候補を両fidelityで再評価すると順位が反転する。low fidelityだけで推薦を確定しない。"
        ),
        summary_en=(
            "Re-evaluating two candidates at both fidelities reverses their ordering; "
            "do not finalize a recommendation from low fidelity alone."
        ),
        limitations_ja=(
            "意図的な1次元biasの最小教材であり、"
            "実simulatorのdiscrepancy modelや発生頻度を表さない。"
        ),
        limitations_en=(
            "A minimal one-dimensional example with intentional bias; it does not "
            "represent a real simulator discrepancy model or event frequency."
        ),
    )
    observed_value = VisualizationObservable(
        observable_id="observed_value",
        label_ja="fidelity別の観測値",
        label_en="observed value by fidelity",
    )
    lesson = generated.scenario.lesson.model_copy(
        update={
            "failure_signals": [
                VisualizationSignal(
                    signal_id="low_high_candidate_order_reverses",
                    label_ja="同じ2候補の順位がlow/high fidelityで反転する",
                    label_en="The same two candidates reverse order across fidelities",
                    observable_ids=["evaluation_ledger", "fidelity", "observed_value"],
                )
            ],
            "primary_observables": [
                *generated.scenario.lesson.primary_observables,
                observed_value,
            ],
            "narration_steps": [
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="2候補のlow fidelity観測を比べる",
                    title_en="Compare low-fidelity observations at two candidates",
                    observable_ids=["evaluation_ledger", "fidelity", "observed_value"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="同じ候補をhigh fidelityで確認する",
                    title_en="Check the same candidates at high fidelity",
                    observable_ids=["evaluation_ledger", "fidelity", "observed_value"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="low/highの候補順位が反転する箇所を読む",
                    title_en="Read where candidate ordering reverses across fidelities",
                    observable_ids=["fidelity", "observed_value"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="high fidelity確認前に推薦を確定しない",
                    title_en="Do not finalize the recommendation before high-fidelity checks",
                    observable_ids=["evaluation_ledger", "best_so_far"],
                ),
            ],
        }
    )
    artifact = generated.scenario.artifact.model_copy(
        update={
            "observable_ids": [
                *generated.scenario.artifact.observable_ids,
                observed_value.observable_id,
            ]
        }
    )
    scenario = generated.scenario.model_copy(update={"lesson": lesson, "artifact": artifact})
    scenario = VisualizationScenario.model_validate(scenario.model_dump(mode="json"))
    return GeneratedSurrogateScenario(
        scenario=scenario,
        payload=generated.payload,
        payload_bytes=generated.payload_bytes,
    )


def write_surrogate_scenarios(
    output_dir: Path, *, dataset_version: str
) -> list[VisualizationScenario]:
    scenarios: list[VisualizationScenario] = []
    for strategy in ("exploit", "explore"):
        for noise_preset in ("noiseless", "small_noise"):
            generated = generate_surrogate_scenario(
                dataset_version=dataset_version,
                strategy=strategy,
                noise_preset=noise_preset,
            )
            target = output_dir / generated.scenario.artifact.payload_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(generated.payload_bytes)
            scenarios.append(generated.scenario)
    for generator in (
        generate_evaluation_ledger_scenario,
        generate_high_fidelity_baseline_scenario,
        generate_low_fidelity_bias_scenario,
    ):
        generated = generator(dataset_version=dataset_version)
        target = output_dir / generated.scenario.artifact.payload_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(generated.payload_bytes)
        scenarios.append(generated.scenario)
    return scenarios
