from __future__ import annotations

import json
import math
import random
from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Observation(ScenarioModel):
    x: float
    value: float
    observed_value: float


class PredictivePoint(ScenarioModel):
    x: float
    true_value: float
    mean: float
    lower: float
    upper: float
    acquisition: float = Field(ge=0)


class SurrogateFrame(ScenarioModel):
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


class FairnessEnvelope(ScenarioModel):
    budget: int = Field(gt=0)
    initial_design: list[float]
    objective_id: str
    domain: list[float]
    seed: int
    comparison_method_id: Literal["M_RANDOM_SEARCH"]


class SurrogateUncertaintyPayload(ScenarioModel):
    renderer_family: Literal["surrogate_uncertainty"] = "surrogate_uncertainty"
    renderer_contract_version: Literal["1.0.0"] = "1.0.0"
    artifact_kind: Literal["executable_trace"] = "executable_trace"
    method_id: Literal["M_BAYESIAN_OPT_GP"] = "M_BAYESIAN_OPT_GP"
    comparison_method_id: Literal["M_RANDOM_SEARCH"] = "M_RANDOM_SEARCH"
    acquisition_id: Literal["expected_improvement"] = "expected_improvement"
    strategy: Literal["exploit", "explore"]
    noise_preset: Literal["noiseless", "small_noise"]
    seed: int
    noise_std: float = Field(ge=0)
    exploration_xi: float = Field(ge=0)
    initial_design: list[float]
    evaluation_budget: int = Field(gt=0)
    domain: list[float]
    objective_expression: str
    truth_disclosure_ja: str
    frames: list[SurrogateFrame]
    random_history: list[Observation]
    fairness: FairnessEnvelope
    limitations_ja: list[str]

    @model_validator(mode="after")
    def validate_frames(self) -> SurrogateUncertaintyPayload:
        if [frame.frame_index for frame in self.frames] != list(range(len(self.frames))):
            raise ValueError("frames must have consecutive frame_index values")
        if self.frames[-1].oracle_evaluations != self.evaluation_budget:
            raise ValueError("final frame must consume the evaluation budget")
        if len(self.random_history) != self.evaluation_budget:
            raise ValueError("random comparison must use the same evaluation budget")
        return self


class VisualizationScenario(ScenarioModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str
    data_version: Literal["1.0.0"] = "1.0.0"
    scenario_id: str
    title_ja: str
    title_en: str
    purpose: Literal["method_intuition", "sensitivity", "failure_mode"]
    problem_definition_id: str
    problem_instance_id: str
    lesson_id: str
    experiment_id: str
    run_id: str
    artifact_id: str
    artifact_kind: Literal["executable_trace"] = "executable_trace"
    source_ids: list[str]
    last_verified: str
    payload: SurrogateUncertaintyPayload


class ScenarioIndexEntry(ScenarioModel):
    scenario_id: str
    title_ja: str
    strategy: Literal["exploit", "explore"]
    noise_preset: Literal["noiseless", "small_noise"]
    path: str
    bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class VisualizationScenarioIndex(ScenarioModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str
    data_version: Literal["1.0.0"] = "1.0.0"
    scenarios: list[ScenarioIndexEntry]


def canonical_scenario_bytes(model: ScenarioModel) -> bytes:
    payload = json.dumps(
        model.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return (payload + "\n").encode()


def educational_objective(x: float) -> float:
    return 0.16 * (x - 1.7) ** 2 + 0.45 * math.sin(2.2 * x) + 0.12 * math.sin(5.3 * x)


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
        variance = max(1e-8, 1.0 - sum(left * right for left, right in zip(k, solved, strict=True)))
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


def generate_bo_scenario(
    *,
    dataset_version: str,
    strategy: Literal["exploit", "explore"],
    noise_preset: Literal["noiseless", "small_noise"],
) -> VisualizationScenario:
    seed = 2604
    rng = random.Random(seed + (17 if noise_preset == "small_noise" else 0))
    noise_std = 0.08 if noise_preset == "small_noise" else 0.0
    xi = 0.18 if strategy == "explore" else 0.0
    budget = 10
    initial_design = [-2.6, 0.0, 2.6]
    grid = [round(-3.0 + index * 0.075, 6) for index in range(81)]
    random_rng = random.Random(seed)
    random_noise_rng = random.Random(seed + 991 + (17 if noise_preset == "small_noise" else 0))
    random_xs = [
        *initial_design,
        *[random_rng.uniform(-3.0, 3.0) for _ in range(budget - len(initial_design))],
    ]
    random_history = [
        Observation(
            x=x,
            value=educational_objective(x),
            observed_value=educational_objective(x)
            + (random_noise_rng.gauss(0.0, noise_std) if noise_std else 0.0),
        )
        for x in random_xs
    ]

    def observe(x: float) -> Observation:
        truth = educational_objective(x)
        measured = truth + (rng.gauss(0.0, noise_std) if noise_std else 0.0)
        return Observation(x=x, value=truth, observed_value=measured)

    observations = [observe(x) for x in initial_design]
    frames: list[SurrogateFrame] = []
    while True:
        posterior = _posterior(observations, grid, noise_std)
        incumbent_observation = min(observations, key=lambda item: item.observed_value)
        observed_xs = {round(item.x, 6) for item in observations}
        points: list[PredictivePoint] = []
        for x, (mean, sigma) in zip(grid, posterior, strict=True):
            acquisition = (
                0.0
                if round(x, 6) in observed_xs
                else _expected_improvement(mean, sigma, incumbent_observation.observed_value, xi)
            )
            points.append(
                PredictivePoint(
                    x=x,
                    true_value=educational_objective(x),
                    mean=mean,
                    lower=mean - 1.96 * sigma,
                    upper=mean + 1.96 * sigma,
                    acquisition=acquisition,
                )
            )
        selected = (
            max(points, key=lambda item: (item.acquisition, -abs(item.x)))
            if len(observations) < budget
            else None
        )
        random_incumbent = min(item.observed_value for item in random_history[: len(observations)])
        frame_index = len(frames)
        reason = (
            f"期待改善量 EI={selected.acquisition:.3f} が最大の x={selected.x:.2f} を次に選択。"
            f"予測平均 {selected.mean:.3f} と不確実性幅 "
            f"{selected.upper - selected.mean:.3f} の両方が選択理由です。"
            if selected
            else "評価予算を使い切りました。観測済みの最良値を最終 incumbent とします。"
        )
        frames.append(
            SurrogateFrame(
                frame_index=frame_index,
                oracle_evaluations=len(observations),
                observations=list(observations),
                predictive_summary=points,
                selected_point=selected.x if selected else None,
                selected_mean=selected.mean if selected else None,
                selected_uncertainty=(selected.upper - selected.mean) if selected else None,
                selected_acquisition=selected.acquisition if selected else None,
                incumbent_x=incumbent_observation.x,
                incumbent_value=incumbent_observation.observed_value,
                random_incumbent_value=random_incumbent,
                explanation_ja=reason,
            )
        )
        if selected is None:
            break
        observations.append(observe(selected.x))

    scenario_id = f"SCENARIO_BO_1D_{strategy.upper()}_{noise_preset.upper()}"
    return VisualizationScenario(
        dataset_version=dataset_version,
        scenario_id=scenario_id,
        title_ja=f"高価な1次元black-box: {strategy} / {noise_preset}",
        title_en=f"Expensive 1D black box: {strategy} / {noise_preset}",
        purpose="sensitivity",
        problem_definition_id="PROBLEM_EXPENSIVE_BLACK_BOX_1D",
        problem_instance_id="INSTANCE_EDUCATIONAL_WAVY_1D",
        lesson_id="LESSON_BO_EXPLORE_EXPLOIT",
        experiment_id="EXPERIMENT_BO_EQUAL_BUDGET",
        run_id=f"RUN_BO_{strategy}_{noise_preset}_2604",
        artifact_id=f"ARTIFACT_BO_{strategy}_{noise_preset}_2604",
        source_ids=["S035", "S059", "S075"],
        last_verified="2026-07-15",
        payload=SurrogateUncertaintyPayload(
            strategy=strategy,
            noise_preset=noise_preset,
            seed=seed,
            noise_std=noise_std,
            exploration_xi=xi,
            initial_design=initial_design,
            evaluation_budget=budget,
            domain=[-3.0, 3.0],
            objective_expression="0.16(x-1.7)^2 + 0.45 sin(2.2x) + 0.12 sin(5.3x)",
            truth_disclosure_ja="破線の真の目的関数は教材用の答え合わせです。optimizerは観測点以外の真値を参照しません。",
            frames=frames,
            random_history=random_history,
            fairness=FairnessEnvelope(
                budget=budget,
                initial_design=initial_design,
                objective_id="OBJECTIVE_EDUCATIONAL_WAVY_1D",
                domain=[-3.0, 3.0],
                seed=seed,
                comparison_method_id="M_RANDOM_SEARCH",
            ),
            limitations_ja=[
                "surrogateのkernelやnoise仮定が外れると、不確実性もacquisitionも誤誘導されます。",
                "高次元では候補空間と必要観測数が急増します。低有効次元や構造化kernelを検討してください。",
                "有限予算の最良観測は大域最適性の証明ではありません。",
            ],
        ),
    )


def write_visualization_scenarios(
    output_dir: Path, *, dataset_version: str
) -> tuple[str, int, str]:
    directory = output_dir / "visualizations"
    directory.mkdir(parents=True, exist_ok=True)
    entries: list[ScenarioIndexEntry] = []
    for strategy in ("exploit", "explore"):
        for noise_preset in ("noiseless", "small_noise"):
            scenario = generate_bo_scenario(
                dataset_version=dataset_version, strategy=strategy, noise_preset=noise_preset
            )
            filename = f"bo-{strategy}-{noise_preset}.json"
            payload = canonical_scenario_bytes(scenario)
            (directory / filename).write_bytes(payload)
            entries.append(
                ScenarioIndexEntry(
                    scenario_id=scenario.scenario_id,
                    title_ja=scenario.title_ja,
                    strategy=strategy,
                    noise_preset=noise_preset,
                    path=filename,
                    bytes=len(payload),
                    sha256=sha256(payload).hexdigest(),
                )
            )
    index = VisualizationScenarioIndex(dataset_version=dataset_version, scenarios=entries)
    index_bytes = canonical_scenario_bytes(index)
    (directory / "index.json").write_bytes(index_bytes)
    return "visualizations/index.json", len(index_bytes), sha256(index_bytes).hexdigest()
