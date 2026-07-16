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


class SurrogateUncertaintyPayload(RendererModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    strategy: Strategy
    noise_preset: NoisePreset
    noise_std: float = Field(ge=0)
    exploration_xi: float = Field(ge=0)
    domain: list[float] = Field(min_length=2, max_length=2)
    objective_expression: str = Field(min_length=1)
    truth_disclosure_ja: str = Field(min_length=1)
    frames: list[SurrogateFrame] = Field(min_length=1)
    random_history: list[Observation] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_frames(self) -> Self:
        if [frame.frame_index for frame in self.frames] != list(range(len(self.frames))):
            raise ValueError("frames must have consecutive frame_index values")
        final_budget = self.frames[-1].oracle_evaluations
        if len(self.random_history) != final_budget:
            raise ValueError("random comparison must use the same evaluation budget")
        if any(frame.oracle_evaluations != frame.frame_index + 3 for frame in self.frames):
            raise ValueError("frames must advance one oracle evaluation at a time")
        return self


@dataclass(frozen=True)
class GeneratedSurrogateScenario:
    scenario: VisualizationScenario
    payload: SurrogateUncertaintyPayload
    payload_bytes: bytes


def canonical_renderer_bytes(model: RendererModel) -> bytes:
    payload = _canonicalize_floats(model.model_dump(mode="json"))
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
    return scenarios
