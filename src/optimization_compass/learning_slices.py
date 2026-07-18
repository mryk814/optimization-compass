from __future__ import annotations

import json
import math
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from optimization_compass.problem_registry import get_runtime_problem
from optimization_compass.trace_models import NonBlank, TraceModel
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

CANONICAL_FLOAT_SIGNIFICANT_DIGITS = 8
CANONICAL_FLOAT_ZERO_TOLERANCE = 1e-9

LAST_VERIFIED = "2026-07-15"
CONSTRAINED_ARTIFACT_ID: Literal["constrained-disk-feasible-region"] = (
    "constrained-disk-feasible-region"
)
PARETO_ARTIFACT_ID: Literal["biobjective-quadratic-pareto-front"] = (
    "biobjective-quadratic-pareto-front"
)
CONSTRAINED_SCENARIO_ID = "SCENARIO_CONSTRAINED_DISK"
CONSTRAINED_FEASIBLE_PATH_SCENARIO_ID = "SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH"
PARETO_SCENARIO_ID = "SCENARIO_BIOBJECTIVE_QUADRATIC"
PARETO_PREFERENCE_SCENARIO_ID = "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY"
TOPOLOGY_ARTIFACT_ID: Literal["topology-optimization-field-evolution"] = (
    "topology-optimization-field-evolution"
)
TOPOLOGY_SCENARIO_ID = "SCENARIO_TOPOLOGY_SIMP_OC"
TOPOLOGY_FAILURE_SCENARIO_ID = "SCENARIO_TOPOLOGY_CHECKERBOARD"


class PlotBounds(TraceModel):
    x: tuple[float, float]
    y: tuple[float, float]


class ConstraintGeometry(TraceModel):
    constraint_id: NonBlank
    kind: Literal["disk"]
    center: tuple[float, float]
    radius: float = Field(gt=0)
    sense: Literal["lte"]
    expression: NonBlank


class FeasibleStep(TraceModel):
    step: int = Field(ge=0)
    point: tuple[float, float]
    objective: float
    constraint_value: float
    violation: float = Field(ge=0)
    feasible: bool
    active_constraint: bool
    label_ja: NonBlank


class FeasiblePath(TraceModel):
    path_id: NonBlank
    method_id: NonBlank
    label_ja: NonBlank
    role: Literal["constraint_aware", "unconstrained_failure"]
    execution_kind: Literal["executable_teaching_trace"]
    steps: list[FeasibleStep] = Field(min_length=2)
    termination_reason_ja: NonBlank


class FeasibleRegionArtifact(TraceModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: NonBlank
    artifact_id: Literal["constrained-disk-feasible-region"]
    artifact_kind: Literal["executable_trace"]
    renderer_family: Literal["feasible_region"]
    problem_definition_id: Literal["PROBLEM_CONSTRAINED_CONTINUOUS_2D"]
    problem_instance_id: Literal["INSTANCE_CONSTRAINED_DISK_2D"]
    objective_direction: Literal["minimize"]
    objective_expression: NonBlank
    bounds: PlotBounds
    constraint: ConstraintGeometry
    contour_values: list[float] = Field(min_length=3)
    known_reference: dict[str, object]
    initial_point: tuple[float, float]
    best_feasible_point: tuple[float, float]
    active_constraint_id: NonBlank
    paths: list[FeasiblePath] = Field(min_length=2)
    method_distinctions_ja: list[NonBlank] = Field(min_length=3)
    text_alternative_ja: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_paths(self) -> Self:
        if {path.role for path in self.paths} != {
            "constraint_aware",
            "unconstrained_failure",
        }:
            raise ValueError("feasible-region artifact requires primary and failure paths")
        primary = next(path for path in self.paths if path.role == "constraint_aware")
        if not any(step.active_constraint for step in primary.steps):
            raise ValueError("constraint-aware path must identify an active constraint")
        failure = next(path for path in self.paths if path.role == "unconstrained_failure")
        if not any(not step.feasible for step in failure.steps[1:]):
            raise ValueError("failure path must demonstrate an infeasible iterate")
        return self


class TopologyGrid(TraceModel):
    columns: int = Field(ge=2, le=32)
    rows: int = Field(ge=2, le=32)


class TopologyStep(TraceModel):
    iteration: int = Field(ge=0)
    density: list[float] = Field(min_length=1)
    displacement_field: list[float] = Field(min_length=1)
    strain_energy_field: list[float] = Field(min_length=1)
    sensitivity_raw: list[float] = Field(min_length=1)
    sensitivity_filtered: list[float] = Field(min_length=1)
    volume_fraction: float = Field(ge=0, le=1)
    compliance: float = Field(ge=0)
    gray_fraction: float = Field(ge=0, le=1)
    checkerboard_score: float = Field(ge=0)
    projection_beta: float = Field(gt=0)
    label_ja: NonBlank


class TopologyRun(TraceModel):
    run_id: NonBlank
    method_id: NonBlank
    label_ja: NonBlank
    role: Literal["primary", "comparison", "failure_contrast"]
    steps: list[TopologyStep] = Field(min_length=2)
    termination_reason_ja: NonBlank


class TopologyFieldArtifact(TraceModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: NonBlank
    artifact_id: Literal["topology-optimization-field-evolution"]
    artifact_kind: Literal["executable_trace"]
    renderer_family: Literal["field_evolution"]
    problem_definition_id: Literal["PROBLEM_TOPOLOGY_OPTIMIZATION"]
    problem_instance_id: Literal["INSTANCE_TOPOLOGY_CANTILEVER_2D"]
    objective_expression: NonBlank
    state_equation: NonBlank
    grid: TopologyGrid
    volume_fraction_target: float = Field(gt=0, lt=1)
    load_description: NonBlank
    runs: list[TopologyRun] = Field(min_length=3)
    method_distinctions_ja: list[NonBlank] = Field(min_length=4)
    text_alternative_ja: NonBlank
    limitations_ja: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_fields(self) -> Self:
        cell_count = self.grid.columns * self.grid.rows
        roles = {run.role for run in self.runs}
        if roles != {"primary", "comparison", "failure_contrast"}:
            raise ValueError("topology artifact requires primary, comparison, and failure runs")
        for run in self.runs:
            for step in run.steps:
                for field in (
                    step.density,
                    step.displacement_field,
                    step.strain_energy_field,
                    step.sensitivity_raw,
                    step.sensitivity_filtered,
                ):
                    if len(field) != cell_count:
                        raise ValueError("topology field length must match grid size")
        failure = next(run for run in self.runs if run.role == "failure_contrast")
        primary = next(run for run in self.runs if run.role == "primary")
        if failure.steps[-1].checkerboard_score <= primary.steps[-1].checkerboard_score:
            raise ValueError("failure run must expose a higher checkerboard score")
        return self


class ObjectivePoint(TraceModel):
    point_id: NonBlank
    decision: tuple[float, float]
    objectives: tuple[float, float]
    dominated: bool


class ParetoReference(TraceModel):
    ideal: tuple[float, float]
    nadir: tuple[float, float]
    ideal_is_feasible: bool
    status: Literal["known_exact"]


class PreferenceSelection(TraceModel):
    weight_f1: float = Field(ge=0, le=1)
    decision: tuple[float, float]
    objectives: tuple[float, float]


class TriObjectivePoint(TraceModel):
    point_id: NonBlank
    decision: tuple[float, float]
    objectives: tuple[float, float, float]
    dominated: bool


class TriObjectiveReference(TraceModel):
    ideal: tuple[float, float, float]
    nadir: tuple[float, float, float]
    ideal_is_feasible: bool
    status: Literal["sampled_grid"]


class TriObjectiveLens(TraceModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    derivation_status: Literal["sampled_teaching_extension"]
    objective_directions: tuple[Literal["minimize"], Literal["minimize"], Literal["minimize"]]
    axis_labels: tuple[NonBlank, NonBlank, NonBlank]
    objective_expressions: tuple[NonBlank, NonBlank, NonBlank]
    points: list[TriObjectivePoint] = Field(min_length=10)
    pareto_front: list[TriObjectivePoint] = Field(min_length=5)
    reference: TriObjectiveReference
    text_alternative_ja: NonBlank
    limitations_ja: NonBlank


class ParetoFrontArtifact(TraceModel):
    contract_version: Literal["1.1.0"] = "1.1.0"
    dataset_version: NonBlank
    artifact_id: Literal["biobjective-quadratic-pareto-front"]
    artifact_kind: Literal["result_visualization"]
    execution_status: Literal["executable_result"]
    renderer_family: Literal["pareto_front"]
    problem_definition_id: Literal["PROBLEM_BIOBJECTIVE_CONTINUOUS"]
    problem_instance_id: Literal["INSTANCE_BIOBJECTIVE_QUADRATIC_2D"]
    objective_directions: tuple[Literal["minimize"], Literal["minimize"]]
    axis_labels: tuple[NonBlank, NonBlank]
    points: list[ObjectivePoint] = Field(min_length=10)
    pareto_front: list[ObjectivePoint] = Field(min_length=5)
    preference_selections: list[PreferenceSelection] = Field(min_length=3)
    reference: ParetoReference
    triobjective_lens: TriObjectiveLens
    weighted_sum_limitation_ja: NonBlank
    text_alternative_ja: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_front(self) -> Self:
        if any(point.dominated for point in self.pareto_front):
            raise ValueError("Pareto front cannot contain dominated points")
        if not any(point.dominated for point in self.points):
            raise ValueError("Pareto artifact must include dominated contrast points")
        if any(point.dominated for point in self.triobjective_lens.pareto_front):
            raise ValueError("tri-objective sampled front cannot contain dominated points")
        if not any(point.dominated for point in self.triobjective_lens.points):
            raise ValueError("tri-objective lens must include dominated contrast points")
        return self


class LearningSliceLink(TraceModel):
    artifact_id: NonBlank
    scenario_id: NonBlank
    label: NonBlank
    route: NonBlank
    method_ids: list[NonBlank] = Field(min_length=1)
    source_ids: list[NonBlank] = Field(min_length=1)
    view_ids: list[NonBlank] = Field(min_length=1)
    last_verified: date


def generate_topology_field_artifact(dataset_version: str) -> TopologyFieldArtifact:
    """Generate a small deterministic field trace for the topology journey.

    This is intentionally a teaching generator: it exposes the state,
    sensitivity, filtering, and update loop on a fixed 8x4 grid. It is not a
    production FEM solver and the payload says so explicitly.
    """
    columns, rows, target_volume = 8, 4, 0.5
    target = _topology_smooth_target(columns, rows)
    checkerboard = [
        _clamp(0.5 + 0.34 * (1.0 if (x + y) % 2 == 0 else -1.0))
        for y in range(rows)
        for x in range(columns)
    ]
    primary = _topology_run(
        run_id="topology-oc",
        method_id="M_OC_TOPOLOGY",
        label_ja="OC + filter + projection",
        role="primary",
        target=target,
        columns=columns,
        rows=rows,
        volume_fraction=target_volume,
        update_rate=0.18,
        filter_radius=1.5,
        projection=True,
        max_iterations=12,
    )
    comparison = _topology_run(
        run_id="topology-mma",
        method_id="M_MMA",
        label_ja="MMA-style conservative update",
        role="comparison",
        target=[_clamp(0.85 * value + 0.075) for value in target],
        columns=columns,
        rows=rows,
        volume_fraction=target_volume,
        update_rate=0.12,
        filter_radius=1.5,
        projection=True,
        max_iterations=12,
    )
    failure = _topology_run(
        run_id="topology-no-filter",
        method_id="M_SIMP_TOPOLOGY",
        label_ja="filterなしのfailure contrast",
        role="failure_contrast",
        target=checkerboard,
        columns=columns,
        rows=rows,
        volume_fraction=target_volume,
        update_rate=0.26,
        filter_radius=0.0,
        projection=False,
        max_iterations=12,
    )
    return TopologyFieldArtifact(
        dataset_version=dataset_version,
        artifact_id=TOPOLOGY_ARTIFACT_ID,
        artifact_kind="executable_trace",
        renderer_family="field_evolution",
        problem_definition_id="PROBLEM_TOPOLOGY_OPTIMIZATION",
        problem_instance_id="INSTANCE_TOPOLOGY_CANTILEVER_2D",
        objective_expression="min c(ρ)=Fᵀu, K(ρ)u=F, Eₑ=Emin+ρₑᵖ(E₀−Emin)",
        state_equation=(
            "K(ρ)u=F; compliance c=Fᵀu; sensitivity is obtained through the state/adjoint relation"
        ),
        grid=TopologyGrid(columns=columns, rows=rows),
        volume_fraction_target=target_volume,
        load_description="左端を固定し、右端下側へ下向き荷重を置く片持ちはりの教育用配置。",
        runs=[primary, comparison, failure],
        method_distinctions_ja=[
            "設計field ρ、状態field u、感度 dc/dρ、更新則を別々の観測値として表示します。",
            "filter前の感度とfilter後の感度を分け、近傍平均が更新方向をどう変えるかを追います。",
            (
                "projectionのβは中間密度を押しつぶす強さで、"
                "volume constraintやmesh independenceそのものではありません。"
            ),
            "OCとMMA-style updateは同じ教育用budgetで並べますが、一般性能のrankingではありません。",
        ],
        text_alternative_ja=(
            "OC経路はfilterとprojectionを通して滑らかな密度fieldを作り、"
            "volume fractionを約0.5に保ちます。"
            "filterなしの経路は交互配置のcheckerboardが強くなり、"
            "同じcomplianceの低下だけでは安全な設計と判断できません。"
        ),
        limitations_ja=(
            "8×4要素の決定的な教育用referenceです。実際のQ4 FEM、境界条件、"
            "load case、stress・buckling・manufacturing constraint、"
            "continuous modelの保証、mesh refinement後の同一topologyを示すものではありません。"
        ),
        source_ids=["S097", "S098", "S099", "S100", "S101"],
        last_verified=LAST_VERIFIED,
    )


def _topology_run(
    *,
    run_id: str,
    method_id: str,
    label_ja: str,
    role: Literal["primary", "comparison", "failure_contrast"],
    target: list[float],
    columns: int,
    rows: int,
    volume_fraction: float,
    update_rate: float,
    filter_radius: float,
    projection: bool,
    max_iterations: int,
) -> TopologyRun:
    density = [volume_fraction] * (columns * rows)
    steps: list[TopologyStep] = []
    for iteration in range(max_iterations + 1):
        beta = 1.0 + iteration * 0.65 if projection else 1.0
        raw_sensitivity = [
            -(0.45 + target[index]) / (0.18 + density[index]) ** 2 for index in range(len(density))
        ]
        filtered_sensitivity = (
            _topology_filter(raw_sensitivity, columns, rows, filter_radius)
            if filter_radius > 0
            else list(raw_sensitivity)
        )
        displacement = [
            _clamp(0.15 + 0.7 * math.sqrt(max(value, 0.001)) + 0.08 * (index % columns) / columns)
            for index, value in enumerate(density)
        ]
        strain_energy = [
            max(0.0, (0.25 + target[index]) * displacement[index] ** 2 / (0.12 + density[index]))
            for index in range(len(density))
        ]
        compliance = sum(strain_energy)
        steps.append(
            TopologyStep(
                iteration=iteration,
                density=list(density),
                displacement_field=displacement,
                strain_energy_field=strain_energy,
                sensitivity_raw=raw_sensitivity,
                sensitivity_filtered=filtered_sensitivity,
                volume_fraction=sum(density) / len(density),
                compliance=compliance,
                gray_fraction=sum(4.0 * value * (1.0 - value) for value in density) / len(density),
                checkerboard_score=_checkerboard_score(density, columns, rows),
                projection_beta=beta,
                label_ja="初期field" if iteration == 0 else f"反復 {iteration}",
            )
        )
        if iteration == max_iterations:
            break
        next_density = [
            density[index]
            + update_rate * (target[index] - density[index])
            + 0.025 * filtered_sensitivity[index] / (1.0 + abs(filtered_sensitivity[index]))
            for index in range(len(density))
        ]
        if projection:
            next_density = [
                0.5 + math.tanh(beta * (value - 0.5)) / (2.0 * math.tanh(beta * 0.5))
                for value in next_density
            ]
        density = _normalize_volume([_clamp(value) for value in next_density], volume_fraction)
    return TopologyRun(
        run_id=run_id,
        method_id=method_id,
        label_ja=label_ja,
        role=role,
        steps=steps,
        termination_reason_ja="固定した12反復の教育用budgetを完了しました。",
    )


def _topology_smooth_target(columns: int, rows: int) -> list[float]:
    values: list[float] = []
    for y in range(rows):
        for x in range(columns):
            center = (rows - 1) / 2.0 - 0.65 * x / max(columns - 1, 1)
            load_path = math.exp(-(((y - center) / 0.72) ** 2))
            support_branch = math.exp(-(((y - (rows - 1)) / 0.55) ** 2)) * (x / max(columns - 1, 1))
            values.append(_clamp(0.08 + 0.78 * load_path + 0.16 * support_branch))
    return _normalize_volume(values, 0.5)


def _topology_filter(values: list[float], columns: int, rows: int, radius: float) -> list[float]:
    filtered: list[float] = []
    for index, value in enumerate(values):
        x, y = index % columns, index // columns
        weighted = 0.0
        weight_sum = 0.0
        for other, candidate in enumerate(values):
            ox, oy = other % columns, other // columns
            distance = math.hypot(x - ox, y - oy)
            weight = max(0.0, radius - distance)
            weighted += weight * candidate
            weight_sum += weight
        filtered.append(weighted / weight_sum if weight_sum else value)
    return filtered


def _normalize_volume(values: list[float], target: float) -> list[float]:
    result = list(values)
    for _ in range(16):
        delta = target - sum(result) / len(result)
        result = [_clamp(value + delta) for value in result]
    return result


def _checkerboard_score(values: list[float], columns: int, rows: int) -> float:
    differences = [
        abs(values[index] - values[index + 1])
        for index in range(len(values))
        if index % columns < columns - 1
    ]
    differences.extend(
        abs(values[index] - values[index + columns]) for index in range(len(values) - columns)
    )
    alternating = sum(
        abs(values[index] - values[index + 1])
        for index in range(len(values))
        if index % columns < columns - 1 and (index // columns) % 2 == 0
    )
    return sum(differences) / len(differences) + alternating / max(len(differences), 1)


def _clamp(value: float) -> float:
    return min(0.999, max(0.001, value))


def generate_feasible_region_artifact(dataset_version: str) -> FeasibleRegionArtifact:
    problem = get_runtime_problem("INSTANCE_CONSTRAINED_DISK_2D")
    reference = problem.instance.known_reference
    if reference is None:
        raise ValueError("constrained teaching problem requires a known reference")
    primary_points = [
        (1.8, 1.8),
        (1.45, 1.45),
        (1.05, 1.05),
        (0.65, 0.65),
        (0.35, 0.35),
        (0.2928932188134524, 0.2928932188134524),
    ]
    failure_points = [(1.8, 1.8), (1.4, 1.4), (0.9, 0.9), (0.5, 0.5), (0.15, 0.15), (0.0, 0.0)]
    primary = _feasible_path(
        "constraint-aware",
        "M_SLSQP",
        "制約を評価する教育用Trace",
        "constraint_aware",
        primary_points,
        "既知最適点でinside_diskがactiveになり、目的値とviolationの両方が収束しました。",
    )
    failure = _feasible_path(
        "unconstrained-failure",
        "M_BFGS",
        "制約を無視するfailure contrast",
        "unconstrained_failure",
        failure_points,
        "目的値は下がりましたが、最終点はconstraint violationを持つため解ではありません。",
    )
    return FeasibleRegionArtifact(
        dataset_version=dataset_version,
        artifact_id=CONSTRAINED_ARTIFACT_ID,
        artifact_kind="executable_trace",
        renderer_family="feasible_region",
        problem_definition_id="PROBLEM_CONSTRAINED_CONTINUOUS_2D",
        problem_instance_id="INSTANCE_CONSTRAINED_DISK_2D",
        objective_direction="minimize",
        objective_expression="min x²+y²",
        bounds=PlotBounds(x=(-0.4, 2.4), y=(-0.4, 2.4)),
        constraint=ConstraintGeometry(
            constraint_id="inside_disk",
            kind="disk",
            center=(1.0, 1.0),
            radius=1.0,
            sense="lte",
            expression="(x−1)²+(y−1)² ≤ 1",
        ),
        contour_values=[0.25, 1.0, 2.0, 4.0, 8.0],
        known_reference=reference,
        initial_point=primary.steps[0].point,
        best_feasible_point=primary.steps[-1].point,
        active_constraint_id="inside_disk",
        paths=[primary, failure],
        method_distinctions_ja=[
            "SLSQPは局所二次modelと線形化制約を解くSQP系で、単純な射影法ではありません。",
            "projected法は射影演算が扱える集合で更新点を戻します。",
            "penalty法とinterior-point法は制約違反・境界への近づき方が異なります。",
        ],
        text_alternative_ja=(
            "円の内側が実行可能領域です。制約を評価する経路は境界上の既知最適点へ到達し、"
            "制約を無視する経路は目的値0へ進む一方で円外へ出て実行不可能になります。"
        ),
        source_ids=["S017", "S029", "S030", "S055", "S056", "S064"],
        last_verified=LAST_VERIFIED,
    )


def _feasible_path(
    path_id: str,
    method_id: str,
    label_ja: str,
    role: Literal["constraint_aware", "unconstrained_failure"],
    points: list[tuple[float, float]],
    termination: str,
) -> FeasiblePath:
    steps: list[FeasibleStep] = []
    for index, point in enumerate(points):
        x, y = point
        constraint_value = (x - 1.0) ** 2 + (y - 1.0) ** 2 - 1.0
        violation = 0.0 if constraint_value <= 1e-12 else constraint_value
        steps.append(
            FeasibleStep(
                step=index,
                point=point,
                objective=x * x + y * y,
                constraint_value=constraint_value,
                violation=violation,
                feasible=violation <= 1e-12,
                active_constraint=abs(constraint_value) <= 1e-9,
                label_ja="初期点"
                if index == 0
                else ("終了点" if index == len(points) - 1 else f"反復 {index}"),
            )
        )
    return FeasiblePath(
        path_id=path_id,
        method_id=method_id,
        label_ja=label_ja,
        role=role,
        execution_kind="executable_teaching_trace",
        steps=steps,
        termination_reason_ja=termination,
    )


def generate_pareto_front_artifact(dataset_version: str) -> ParetoFrontArtifact:
    problem = get_runtime_problem("INSTANCE_BIOBJECTIVE_QUADRATIC_2D")
    points: list[ObjectivePoint] = []
    for x_index in range(9):
        for y_index in range(9):
            decision = (x_index / 4.0, y_index / 4.0)
            objectives = problem.objective_value(decision)
            if not isinstance(objectives, tuple):
                raise ValueError("bi-objective problem returned a scalar")
            points.append(
                ObjectivePoint(
                    point_id=f"grid-{x_index}-{y_index}",
                    decision=decision,
                    objectives=(float(objectives[0]), float(objectives[1])),
                    dominated=False,
                )
            )
    classified = [
        point.model_copy(update={"dominated": _is_dominated(point, points)}) for point in points
    ]
    front = []
    for index in range(21):
        t = index / 10.0
        objectives = problem.objective_value((t, t))
        if not isinstance(objectives, tuple):
            raise ValueError("bi-objective problem returned a scalar")
        front.append(
            ObjectivePoint(
                point_id=f"front-{index}",
                decision=(t, t),
                objectives=(float(objectives[0]), float(objectives[1])),
                dominated=False,
            )
        )
    selections = []
    for weight in (0.2, 0.5, 0.8):
        t = 2.0 * (1.0 - weight)
        objectives = problem.objective_value((t, t))
        if not isinstance(objectives, tuple):
            raise ValueError("bi-objective problem returned a scalar")
        selections.append(
            PreferenceSelection(
                weight_f1=weight,
                decision=(t, t),
                objectives=(float(objectives[0]), float(objectives[1])),
            )
        )
    tri_points = [
        TriObjectivePoint(
            point_id=point.point_id,
            decision=point.decision,
            objectives=(
                point.objectives[0],
                point.objectives[1],
                (point.decision[0] - 2.0) ** 2 + point.decision[1] ** 2,
            ),
            dominated=False,
        )
        for point in points
    ]
    tri_classified = [
        point.model_copy(update={"dominated": _is_dominated_three(point, tri_points)})
        for point in tri_points
    ]
    tri_front = [point for point in tri_classified if not point.dominated]
    tri_nadir = (
        max(point.objectives[0] for point in tri_front),
        max(point.objectives[1] for point in tri_front),
        max(point.objectives[2] for point in tri_front),
    )
    return ParetoFrontArtifact(
        dataset_version=dataset_version,
        artifact_id=PARETO_ARTIFACT_ID,
        artifact_kind="result_visualization",
        execution_status="executable_result",
        renderer_family="pareto_front",
        problem_definition_id="PROBLEM_BIOBJECTIVE_CONTINUOUS",
        problem_instance_id="INSTANCE_BIOBJECTIVE_QUADRATIC_2D",
        objective_directions=("minimize", "minimize"),
        axis_labels=("f₁: originからの距離²", "f₂: (2,2)からの距離²"),
        points=classified,
        pareto_front=front,
        preference_selections=selections,
        reference=ParetoReference(
            ideal=(0.0, 0.0), nadir=(8.0, 8.0), ideal_is_feasible=False, status="known_exact"
        ),
        triobjective_lens=TriObjectiveLens(
            derivation_status="sampled_teaching_extension",
            objective_directions=("minimize", "minimize", "minimize"),
            axis_labels=(
                "f₁: originからの距離²",
                "f₂: (2,2)からの距離²",
                "f₃: (2,0)からの距離²",
            ),
            objective_expressions=(
                "f₁=x²+y²",
                "f₂=(x−2)²+(y−2)²",
                "f₃=(x−2)²+y²",
            ),
            points=tri_classified,
            pareto_front=tri_front,
            reference=TriObjectiveReference(
                ideal=(0.0, 0.0, 0.0),
                nadir=tri_nadir,
                ideal_is_feasible=False,
                status="sampled_grid",
            ),
            text_alternative_ja=(
                "3つの二次目的を最小化する同じ81点を目的空間に表示します。"
                "橙の点はpreferenceで選んだ点で、2D投影とparallel coordinatesでも同じ点です。"
            ),
            limitations_ja=(
                "9×9 gridから得たsampled teaching lensです。連続問題の真の3目的Pareto frontや"
                "その曲面形状を保証するものではありません。"
            ),
        ),
        weighted_sum_limitation_ja=(
            "この教材のfrontは凸なのでweighted sumでたどれます。一般の非凸frontでは、"
            "正のweightを変えても取得できない非劣点があるため、front全体の保証にはなりません。"
        ),
        text_alternative_ja=(
            "両目的を最小化する81個の実行結果を目的空間に表示します。灰色は支配される点、"
            "緑の曲線は既知Pareto front、橙は選択中のweightで選ばれる非劣点です。"
        ),
        source_ids=["S039", "S055", "S068"],
        last_verified=LAST_VERIFIED,
    )


def _is_dominated(candidate: ObjectivePoint, points: list[ObjectivePoint]) -> bool:
    c1, c2 = candidate.objectives
    return any(
        (p1 <= c1 and p2 <= c2) and (p1 < c1 or p2 < c2)
        for point in points
        if point.point_id != candidate.point_id
        for p1, p2 in [point.objectives]
    )


def _is_dominated_three(candidate: TriObjectivePoint, points: list[TriObjectivePoint]) -> bool:
    return any(
        all(value <= candidate.objectives[index] for index, value in enumerate(point.objectives))
        and any(value < candidate.objectives[index] for index, value in enumerate(point.objectives))
        for point in points
        if point.point_id != candidate.point_id
    )


def write_learning_slice_scenarios(
    output_dir: Path, *, dataset_version: str
) -> tuple[list[VisualizationScenario], list[LearningSliceLink]]:
    feasible = generate_feasible_region_artifact(dataset_version)
    pareto = generate_pareto_front_artifact(dataset_version)
    topology = generate_topology_field_artifact(dataset_version)
    payloads: list[tuple[TraceModel, str]] = [
        (feasible, f"visualizations/{CONSTRAINED_ARTIFACT_ID}.json"),
        (pareto, f"visualizations/{PARETO_ARTIFACT_ID}.json"),
        (topology, f"visualizations/{TOPOLOGY_ARTIFACT_ID}.json"),
    ]
    payload_metadata: dict[str, tuple[int, str]] = {}
    for artifact, relative_path in payloads:
        payload = _canonical_bytes(
            artifact,
            canonicalize_floats=relative_path == f"visualizations/{TOPOLOGY_ARTIFACT_ID}.json",
        )
        path = output_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        payload_metadata[relative_path] = (len(payload), sha256(payload).hexdigest())
    constrained_failure = _constrained_scenario(dataset_version, payload_metadata)
    pareto_primary = _pareto_scenario(dataset_version, payload_metadata)
    topology_primary = _topology_scenario(dataset_version, payload_metadata)
    scenarios = [
        _constrained_feasible_path_scenario(constrained_failure),
        constrained_failure,
        pareto_primary,
        _pareto_preference_scenario(pareto_primary),
        topology_primary,
        _topology_failure_scenario(topology_primary),
    ]
    links = [
        LearningSliceLink(
            artifact_id=CONSTRAINED_ARTIFACT_ID,
            scenario_id=CONSTRAINED_SCENARIO_ID,
            label="制約付き最適化: feasible region",
            route=f"/theater/learning/{CONSTRAINED_SCENARIO_ID}",
            method_ids=["M_SLSQP", "M_BFGS"],
            source_ids=list(feasible.source_ids),
            view_ids=["VIEW_PROBLEM_STRUCTURE", "VIEW_METHOD_MECHANISM"],
            last_verified=date.fromisoformat(LAST_VERIFIED),
        ),
        LearningSliceLink(
            artifact_id=PARETO_ARTIFACT_ID,
            scenario_id=PARETO_SCENARIO_ID,
            label="多目的最適化: Pareto front",
            route=f"/theater/learning/{PARETO_SCENARIO_ID}",
            method_ids=["M_NSGA_II", "M_WEIGHTED_SUM"],
            source_ids=list(pareto.source_ids),
            view_ids=["VIEW_PROBLEM_STRUCTURE", "VIEW_METHOD_MECHANISM"],
            last_verified=date.fromisoformat(LAST_VERIFIED),
        ),
        LearningSliceLink(
            artifact_id=TOPOLOGY_ARTIFACT_ID,
            scenario_id=TOPOLOGY_SCENARIO_ID,
            label="構造トポロジー最適化: field evolution",
            route=f"/theater/learning/{TOPOLOGY_SCENARIO_ID}",
            method_ids=[
                "M_SIMP_TOPOLOGY",
                "M_DENSITY_FILTER",
                "M_OC_TOPOLOGY",
                "M_MMA",
                "M_ADJOINT_SENSITIVITY",
            ],
            source_ids=list(topology.source_ids),
            view_ids=["VIEW_PROBLEM_STRUCTURE", "VIEW_METHOD_MECHANISM"],
            last_verified=date.fromisoformat(LAST_VERIFIED),
        ),
    ]
    return scenarios, links


def _topology_scenario(
    dataset_version: str, payload_metadata: dict[str, tuple[int, str]]
) -> VisualizationScenario:
    path = f"visualizations/{TOPOLOGY_ARTIFACT_ID}.json"
    size, digest = payload_metadata[path]
    observables = [
        VisualizationObservable(
            observable_id="density_field",
            label_ja="設計密度field",
            label_en="design density field",
        ),
        VisualizationObservable(
            observable_id="displacement_field",
            label_ja="変位field",
            label_en="displacement field",
        ),
        VisualizationObservable(
            observable_id="strain_energy_field",
            label_ja="ひずみエネルギーfield",
            label_en="strain-energy field",
        ),
        VisualizationObservable(
            observable_id="sensitivity_raw",
            label_ja="未処理感度",
            label_en="raw sensitivity",
        ),
        VisualizationObservable(
            observable_id="sensitivity_filtered",
            label_ja="filter後の感度",
            label_en="filtered sensitivity",
        ),
        VisualizationObservable(
            observable_id="volume_fraction",
            label_ja="体積率",
            label_en="volume fraction",
        ),
        VisualizationObservable(
            observable_id="compliance",
            label_ja="コンプライアンス",
            label_en="compliance",
        ),
        VisualizationObservable(
            observable_id="gray_fraction",
            label_ja="gray fraction",
            label_en="gray fraction",
        ),
        VisualizationObservable(
            observable_id="checkerboard_score",
            label_ja="checkerboard score",
            label_en="checkerboard score",
        ),
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=dataset_version,
        scenario_id=TOPOLOGY_SCENARIO_ID,
        identity_status="canonical",
        canonical_scenario_id=TOPOLOGY_SCENARIO_ID,
        title_ja="片持ちはりの設計fieldを更新過程で読む",
        title_en="Read a cantilever design field as it evolves",
        purpose="mechanism",
        problem_definition_id="PROBLEM_TOPOLOGY_OPTIMIZATION",
        problem_instance_id="INSTANCE_TOPOLOGY_CANTILEVER_2D",
        lesson=VisualizationLesson(
            learning_objective=LocalizedText(
                ja="設計密度、状態field、感度、更新則を一つの反復で対応づける",
                en="Relate design density, state fields, sensitivity, and updates in one iteration",
            ),
            misconception=LocalizedText(
                ja="コンプライアンスが下がれば、離散化の癖も消えている",
                en="A falling compliance means discretization artifacts have disappeared",
            ),
            expected_phenomenon_ja=(
                "体積率を保ちながら荷重経路が残り、filterとprojectionの強さに応じて"
                "密度fieldの境界とgray fractionが変わります。"
            ),
            expected_phenomenon_en=(
                "The load path remains under a volume constraint while filtering and "
                "projection change field boundaries and gray fraction."
            ),
            success_signals=[
                VisualizationSignal(
                    signal_id="stable_load_path",
                    label_ja="体積率を保った荷重経路",
                    label_en="load path under the volume target",
                    observable_ids=["density_field", "volume_fraction", "compliance"],
                ),
                VisualizationSignal(
                    signal_id="filtered_sensitivity",
                    label_ja="filter後の感度が更新に反映される",
                    label_en="filtered sensitivity drives the update",
                    observable_ids=["sensitivity_raw", "sensitivity_filtered", "density_field"],
                ),
            ],
            failure_signals=[
                VisualizationSignal(
                    signal_id="checkerboard_artifact",
                    label_ja="低いcomplianceとcheckerboardの併存",
                    label_en="low compliance with a checkerboard artifact",
                    observable_ids=["compliance", "checkerboard_score", "density_field"],
                ),
                VisualizationSignal(
                    signal_id="gray_field",
                    label_ja="gray fractionが残る",
                    label_en="persistent gray density",
                    observable_ids=["gray_fraction", "density_field"],
                ),
            ],
            primary_observables=observables[:7],
            secondary_observables=observables[7:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="一様な初期密度",
                    title_en="Uniform initial density",
                    observable_ids=["density_field", "volume_fraction"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="感度から密度を更新",
                    title_en="Update density from sensitivity",
                    observable_ids=["sensitivity_raw", "sensitivity_filtered", "density_field"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="荷重経路と離散化の癖が分かれる",
                    title_en="Separate load path from discretization artifacts",
                    observable_ids=["density_field", "strain_energy_field", "checkerboard_score"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="体積率と停止理由を確認",
                    title_en="Check volume and termination",
                    observable_ids=["volume_fraction", "compliance", "gray_fraction"],
                ),
            ],
            comparison_role="primary_example",
            prerequisite_concept_ids=["concept.variable-domain", "concept.constraint-class"],
            recommended_next_scenario_ids=[TOPOLOGY_FAILURE_SCENARIO_ID],
            known_reference_display=KnownReferenceDisplay(
                policy="not_shown",
                note_ja="解析解や製造可能な最終形状ではなく、教育用のfield traceを表示します。",
                note_en=(
                    "Show an educational field trace rather than an analytic or "
                    "manufacturable reference."
                ),
            ),
            static_summary=LocalizedText(
                ja="片持ちはりの密度field、状態field、感度、更新指標を反復ごとに並べます。",
                en="Inspect density, state, sensitivity, and update metrics for a cantilever.",
            ),
            text_alternative=LocalizedText(
                ja=(
                    "初期の一様密度から、filter後の感度で密度を更新します。"
                    "OCとMMAは同じ問題と予算で動き、"
                    "filterなしの経路はcheckerboard scoreが高くなります。"
                ),
                en=(
                    "Starting from uniform density, the field is updated from filtered "
                    "sensitivity. OC and MMA share the problem and budget, while the "
                    "unfiltered path develops a higher checkerboard score."
                ),
            ),
            derived_media_caption=LocalizedText(
                ja="片持ちはりのdensity、state、sensitivityのfield evolution",
                en="Density, state, and sensitivity field evolution for a cantilever",
            ),
            limitations_ja=(
                "これは32要素の決定的な教育用traceです。実際の有限要素法の収束、"
                "製造制約、mesh refinement後の同一topology、局所解や大域解を保証しません。"
            ),
            limitations_en=(
                "This is a deterministic educational trace on 32 elements. It does not guarantee "
                "finite-element convergence, manufacturability, topology invariance "
                "under mesh refinement, or global optimality."
            ),
        ),
        experiment=VisualizationExperiment(
            oracle_policy=[
                "objective_value",
                "gradient",
                "constraint_value",
                "constraint_jacobian",
            ],
            initial_condition=VisualizationInitialCondition(point=[0.5] * 32),
            parameter_preset_id="PRESET_TOPOLOGY_CANTILEVER_8X4",
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=12),
            stopping={"max_iterations": 12, "volume_tolerance": 0.001},
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id="RUN_TOPOLOGY_OC",
                method_id="M_OC_TOPOLOGY",
                profile_id="PROFILE_OC_TOPOLOGY_FIELD",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=TOPOLOGY_ARTIFACT_ID,
            ),
            VisualizationRun(
                run_id="RUN_TOPOLOGY_MMA",
                method_id="M_MMA",
                profile_id="PROFILE_MMA_TOPOLOGY_FIELD",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=TOPOLOGY_ARTIFACT_ID,
            ),
            VisualizationRun(
                run_id="RUN_TOPOLOGY_NO_FILTER",
                method_id="M_SIMP_TOPOLOGY",
                profile_id="PROFILE_SIMP_TOPOLOGY_FIELD",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=TOPOLOGY_ARTIFACT_ID,
            ),
        ],
        artifact=VisualizationArtifact(
            artifact_kind="executable_trace",
            artifact_contract="TopologyFieldEvolution",
            artifact_contract_version="1.0.0",
            renderer_family="field_evolution",
            renderer_contract_version="1.0.0",
            observable_ids=[item.observable_id for item in observables],
            payload_path=path,
            payload_bytes=size,
            payload_sha256=digest,
        ),
        source_ids=["S097", "S098", "S099", "S100", "S101"],
        last_verified=LAST_VERIFIED,
    )


def _topology_failure_scenario(primary_scenario: VisualizationScenario) -> VisualizationScenario:
    payload = primary_scenario.model_dump(mode="python")
    lesson = primary_scenario.lesson.model_dump(mode="python")
    lesson.update(
        {
            "learning_objective": {
                "ja": "complianceだけでは判定できないcheckerboard failureを見つける",
                "en": "Find a checkerboard failure that compliance alone cannot diagnose",
            },
            "misconception": {
                "ja": "密度fieldが細かく変化するほど構造を表現できている",
                "en": "Finer density alternation always represents a better structure",
            },
            "expected_phenomenon_ja": (
                "filterを外した経路ではcomplianceが改善しても、隣接要素の交互模様が残り、"
                "checkerboard scoreが上がります。"
            ),
            "expected_phenomenon_en": (
                "Without filtering, compliance may improve while alternating adjacent cells "
                "remain and the checkerboard score rises."
            ),
            "success_signals": [
                {
                    "signal_id": "artifact_is_visible",
                    "label_ja": "checkerboard scoreが可視化される",
                    "label_en": "the checkerboard score is visible",
                    "observable_ids": ["density_field", "checkerboard_score"],
                }
            ],
            "failure_signals": [
                {
                    "signal_id": "compliance_hides_artifact",
                    "label_ja": "complianceだけではartifactを見落とす",
                    "label_en": "compliance hides the artifact",
                    "observable_ids": ["compliance", "checkerboard_score"],
                }
            ],
            "primary_observables": [
                item
                for item in [*lesson["primary_observables"], *lesson["secondary_observables"]]
                if item["observable_id"]
                in {"density_field", "compliance", "checkerboard_score", "volume_fraction"}
            ],
            "secondary_observables": [
                item
                for item in lesson["secondary_observables"]
                if item["observable_id"] in {"gray_fraction", "volume_fraction"}
            ],
            "narration_steps": [
                {
                    "milestone_id": "start",
                    "title_ja": "一様な初期密度",
                    "title_en": "Uniform initial density",
                    "observable_ids": ["density_field", "volume_fraction"],
                },
                {
                    "milestone_id": "first_change",
                    "title_ja": "交互模様が現れる",
                    "title_en": "Alternating cells appear",
                    "observable_ids": ["density_field", "checkerboard_score"],
                },
                {
                    "milestone_id": "pattern_visible",
                    "title_ja": "complianceとartifactを分けて読む",
                    "title_en": "Separate compliance from the artifact",
                    "observable_ids": ["compliance", "checkerboard_score"],
                },
                {
                    "milestone_id": "termination",
                    "title_ja": "filterの必要性を判断",
                    "title_en": "Judge whether filtering is needed",
                    "observable_ids": ["checkerboard_score", "gray_fraction"],
                },
            ],
            "comparison_role": "failure_contrast",
            "recommended_next_scenario_ids": [TOPOLOGY_SCENARIO_ID],
            "static_summary": {
                "ja": (
                    "filterなしの密度更新で、低いcomplianceとcheckerboard artifactが"
                    "同時に現れます。"
                ),
                "en": (
                    "Unfiltered density updates show low compliance together with a "
                    "checkerboard artifact."
                ),
            },
            "text_alternative": {
                "ja": (
                    "filterなしの経路は体積率を保つ一方、交互模様が増え、"
                    "complianceだけでは良し悪しを決められません。"
                ),
                "en": (
                    "The unfiltered path preserves volume but develops alternation, "
                    "so compliance alone is insufficient."
                ),
            },
            "derived_media_caption": {
                "ja": "checkerboard artifactを含む失敗contrast",
                "en": "Failure contrast with a checkerboard artifact",
            },
        }
    )
    payload.update(
        {
            "scenario_id": TOPOLOGY_FAILURE_SCENARIO_ID,
            "identity_status": "derived",
            "canonical_scenario_id": TOPOLOGY_SCENARIO_ID,
            "title_ja": "filterなしのcheckerboard failureを見つける",
            "title_en": "Find the checkerboard failure without filtering",
            "purpose": "failure_contrast",
            "lesson": lesson,
        }
    )
    return VisualizationScenario.model_validate(payload)


def _constrained_scenario(
    dataset_version: str, payload_metadata: dict[str, tuple[int, str]]
) -> VisualizationScenario:
    path = f"visualizations/{CONSTRAINED_ARTIFACT_ID}.json"
    size, digest = payload_metadata[path]
    observables = [
        VisualizationObservable(
            observable_id="objective_contours",
            label_ja="目的関数等高線",
            label_en="objective contours",
        ),
        VisualizationObservable(
            observable_id="feasible_region", label_ja="実行可能領域", label_en="feasible region"
        ),
        VisualizationObservable(
            observable_id="constraint_violation",
            label_ja="制約違反",
            label_en="constraint violation",
        ),
        VisualizationObservable(
            observable_id="active_constraint",
            label_ja="active constraint",
            label_en="active constraint",
        ),
        VisualizationObservable(
            observable_id="termination_reason", label_ja="終了理由", label_en="termination reason"
        ),
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=dataset_version,
        scenario_id=CONSTRAINED_SCENARIO_ID,
        identity_status="canonical",
        canonical_scenario_id=CONSTRAINED_SCENARIO_ID,
        title_ja="実行可能領域と制約を無視した失敗を比べる",
        title_en="Compare a feasible path with an unconstrained failure",
        purpose="failure_contrast",
        problem_definition_id="PROBLEM_CONSTRAINED_CONTINUOUS_2D",
        problem_instance_id="INSTANCE_CONSTRAINED_DISK_2D",
        lesson=VisualizationLesson(
            learning_objective=LocalizedText(
                ja="目的値と実行可能性を別々に読む",
                en="Read objective value and feasibility separately",
            ),
            misconception=LocalizedText(
                ja="目的値が低ければ制約違反点でも良い解である",
                en="A lower objective makes an infeasible point a good solution",
            ),
            expected_phenomenon_ja=(
                "制約対応経路はactive boundaryで止まり、制約無視経路は"
                "低い目的値でもinfeasibleになります。"
            ),
            expected_phenomenon_en=(
                "The constraint-aware path stops on the active boundary while the "
                "unconstrained path becomes infeasible."
            ),
            success_signals=[
                VisualizationSignal(
                    signal_id="feasible_reference",
                    label_ja="violation 0で既知最適点へ到達",
                    label_en="reaches reference with zero violation",
                    observable_ids=["feasible_region", "active_constraint", "constraint_violation"],
                )
            ],
            failure_signals=[
                VisualizationSignal(
                    signal_id="lower_but_invalid",
                    label_ja="目的値は低いがconstraint violationあり",
                    label_en="lower objective with a constraint violation",
                    observable_ids=["objective_contours", "constraint_violation"],
                )
            ],
            primary_observables=observables[:4],
            secondary_observables=observables[4:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="infeasibleな初期点",
                    title_en="Infeasible start",
                    observable_ids=["feasible_region", "constraint_violation"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="実行可能性を回復",
                    title_en="Restore feasibility",
                    observable_ids=["feasible_region", "constraint_violation"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="境界に沿って目的を改善",
                    title_en="Improve along the boundary",
                    observable_ids=["objective_contours", "active_constraint"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="active constraintで終了",
                    title_en="Terminate at active constraint",
                    observable_ids=["active_constraint", "termination_reason"],
                ),
            ],
            comparison_role="failure_contrast",
            prerequisite_concept_ids=["concept.convexity"],
            recommended_next_scenario_ids=[PARETO_SCENARIO_ID],
            known_reference_display=KnownReferenceDisplay(
                policy="show",
                note_ja="解析的な既知最適点とactive constraintを表示します。",
                note_en="Show the analytic optimum and active constraint.",
            ),
            static_summary=LocalizedText(
                ja="円内のfeasible regionと2本の経路を比較します。",
                en="Compare two paths over a disk-shaped feasible region.",
            ),
            text_alternative=LocalizedText(
                ja="制約対応経路は円境界の既知最適点へ、制約無視経路は円外の原点へ進みます。",
                en=(
                    "The constraint-aware path reaches the boundary reference; "
                    "the unconstrained path leaves the disk."
                ),
            ),
            derived_media_caption=LocalizedText(
                ja="feasible region上の制約対応経路とfailure contrast",
                en="Constraint-aware path and failure contrast on a feasible region",
            ),
            limitations_ja=(
                "SLSQPそのものの内部反復を再現せず、canonical problemを使った"
                "決定的な教育用Traceです。"
            ),
            limitations_en=(
                "A deterministic teaching trace on the canonical problem, "
                "not a reproduction of SLSQP internals."
            ),
        ),
        experiment=VisualizationExperiment(
            oracle_policy=[
                "objective_value",
                "gradient",
                "constraint_value",
                "constraint_jacobian",
            ],
            initial_condition=VisualizationInitialCondition(point=[1.8, 1.8]),
            parameter_preset_id="PRESET_CONSTRAINED_DISK_TEACHING",
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=12),
            stopping={"constraint_tolerance": 1e-9, "objective_tolerance": 1e-9},
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id="RUN_CONSTRAINED_AWARE",
                method_id="M_SLSQP",
                profile_id="PROFILE_SLSQP_FEASIBLE_REGION",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=CONSTRAINED_ARTIFACT_ID,
            ),
            VisualizationRun(
                run_id="RUN_UNCONSTRAINED_FAILURE",
                method_id="M_BFGS",
                profile_id="PROFILE_BFGS_FEASIBLE_CONTRAST",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=CONSTRAINED_ARTIFACT_ID,
            ),
        ],
        artifact=VisualizationArtifact(
            artifact_kind="executable_trace",
            artifact_contract="FeasibleRegion",
            artifact_contract_version="1.0.0",
            renderer_family="feasible_region",
            renderer_contract_version="1.0.0",
            observable_ids=[item.observable_id for item in observables],
            payload_path=path,
            payload_bytes=size,
            payload_sha256=digest,
        ),
        source_ids=["S017", "S029", "S030", "S055", "S056", "S064"],
        last_verified=LAST_VERIFIED,
    )


def _constrained_feasible_path_scenario(
    failure_scenario: VisualizationScenario,
) -> VisualizationScenario:
    payload = failure_scenario.model_dump(mode="python")
    lesson = failure_scenario.lesson.model_dump(mode="python")
    lesson.update(
        {
            "learning_objective": {
                "ja": "実行可能性を回復し、制約境界に沿って目的を改善する仕組みを読む",
                "en": (
                    "Read how a constrained path restores feasibility and improves "
                    "along the boundary"
                ),
            },
            "misconception": {
                "ja": "制約付き手法も目的関数の降下方向だけを追えばよい",
                "en": "A constrained method only needs to follow objective descent",
            },
            "expected_phenomenon_ja": (
                "制約対応経路はinfeasibleな初期点から実行可能性を回復し、"
                "active boundaryに沿って既知最適点へ進みます。"
            ),
            "expected_phenomenon_en": (
                "The constraint-aware path restores feasibility from the infeasible start "
                "and follows the active boundary to the known optimum."
            ),
            "failure_signals": [],
            "comparison_role": "primary_example",
            "recommended_next_scenario_ids": [CONSTRAINED_SCENARIO_ID],
            "static_summary": {
                "ja": "円内のfeasible regionで制約対応経路が境界へ進む様子を追います。",
                "en": (
                    "Follow the constraint-aware path to the boundary of a "
                    "disk-shaped feasible region."
                ),
            },
            "text_alternative": {
                "ja": "制約対応経路は円外の初期点から円内へ戻り、円境界の既知最適点へ進みます。",
                "en": (
                    "The constraint-aware path returns from the infeasible start to the disk "
                    "and reaches the boundary reference."
                ),
            },
            "derived_media_caption": {
                "ja": "feasible region上で実行可能性を回復する制約対応経路",
                "en": "Constraint-aware path restoring feasibility on a feasible region",
            },
            "limitations_ja": (
                "同じFeasibleRegion artifactに比較用の制約無視経路も併記します。"
                "SLSQPそのものの内部反復を再現するものではありません。"
            ),
            "limitations_en": (
                "The shared FeasibleRegion artifact also shows the unconstrained contrast path. "
                "This is not a reproduction of SLSQP internals."
            ),
        }
    )
    payload.update(
        {
            "scenario_id": CONSTRAINED_FEASIBLE_PATH_SCENARIO_ID,
            "identity_status": "derived",
            "canonical_scenario_id": CONSTRAINED_SCENARIO_ID,
            "title_ja": "制約を満たす経路で目的を改善する",
            "title_en": "Improve the objective along a constraint-aware path",
            "purpose": "mechanism",
            "lesson": lesson,
            "runs": [failure_scenario.runs[0].model_dump(mode="python")],
        }
    )
    return VisualizationScenario.model_validate(payload)


def _pareto_scenario(
    dataset_version: str, payload_metadata: dict[str, tuple[int, str]]
) -> VisualizationScenario:
    path = f"visualizations/{PARETO_ARTIFACT_ID}.json"
    size, digest = payload_metadata[path]
    observables = [
        VisualizationObservable(
            observable_id="dominated_points", label_ja="支配される点", label_en="dominated points"
        ),
        VisualizationObservable(
            observable_id="pareto_front", label_ja="Pareto front", label_en="Pareto front"
        ),
        VisualizationObservable(
            observable_id="preference_selection",
            label_ja="preferenceで選ぶ点",
            label_en="preference-selected point",
        ),
        VisualizationObservable(
            observable_id="ideal_nadir",
            label_ja="ideal / nadir reference",
            label_en="ideal / nadir reference",
        ),
    ]
    return VisualizationScenario(
        contract_version="1.2.0",
        dataset_version=dataset_version,
        scenario_id=PARETO_SCENARIO_ID,
        identity_status="canonical",
        canonical_scenario_id=PARETO_SCENARIO_ID,
        title_ja="単一bestではなくPareto frontを読む",
        title_en="Read a Pareto front instead of one best value",
        purpose="application_result",
        problem_definition_id="PROBLEM_BIOBJECTIVE_CONTINUOUS",
        problem_instance_id="INSTANCE_BIOBJECTIVE_QUADRATIC_2D",
        lesson=VisualizationLesson(
            learning_objective=LocalizedText(
                ja="支配関係とpreferenceを分けて意思決定する",
                en="Separate dominance from preference",
            ),
            misconception=LocalizedText(
                ja="多目的問題にも全目的で一意なbestがある",
                en="A multi-objective problem has one point best for every objective",
            ),
            expected_phenomenon_ja="非劣点はtrade-off曲線を作り、weightを変えると選択点がfront上を移動します。",
            expected_phenomenon_en=(
                "Non-dominated points form a trade-off curve and preference moves "
                "the selected point."
            ),
            success_signals=[
                VisualizationSignal(
                    signal_id="front_and_selection",
                    label_ja="非劣frontと選択点を区別できる",
                    label_en="distinguishes the front from the selected point",
                    observable_ids=["pareto_front", "preference_selection"],
                )
            ],
            failure_signals=[],
            primary_observables=observables[:3],
            secondary_observables=observables[3:],
            narration_steps=[
                VisualizationNarrationStep(
                    milestone_id="start",
                    title_ja="実行結果を目的空間へ配置",
                    title_en="Plot results in objective space",
                    observable_ids=["dominated_points"],
                ),
                VisualizationNarrationStep(
                    milestone_id="first_change",
                    title_ja="支配される点を除く",
                    title_en="Remove dominated points",
                    observable_ids=["dominated_points", "pareto_front"],
                ),
                VisualizationNarrationStep(
                    milestone_id="pattern_visible",
                    title_ja="trade-off frontを読む",
                    title_en="Read the trade-off front",
                    observable_ids=["pareto_front", "ideal_nadir"],
                ),
                VisualizationNarrationStep(
                    milestone_id="termination",
                    title_ja="preferenceで1点を選ぶ",
                    title_en="Choose with preference",
                    observable_ids=["preference_selection", "ideal_nadir"],
                ),
            ],
            comparison_role="primary_example",
            prerequisite_concept_ids=[],
            recommended_next_scenario_ids=[CONSTRAINED_SCENARIO_ID],
            known_reference_display=KnownReferenceDisplay(
                policy="show",
                note_ja="解析的frontとideal / nadirを表示します。",
                note_en="Show the analytic front and ideal / nadir references.",
            ),
            static_summary=LocalizedText(
                ja="支配点、非劣front、preference選択を同じ目的空間に表示します。",
                en="Plot dominated results, the non-dominated front, and preference selection.",
            ),
            text_alternative=LocalizedText(
                ja="左下方向へ改善する2目的で、緑のfront上に複数のtrade-off候補があります。",
                en=(
                    "For two minimized objectives, multiple trade-off candidates "
                    "lie on the green front."
                ),
            ),
            derived_media_caption=LocalizedText(
                ja="2目的の実行結果と既知Pareto front",
                en="Bi-objective results and the known Pareto front",
            ),
            limitations_ja=(
                "凸で解析的な教材です。weighted sumが非凸frontを欠落させる注意は"
                "一般化上の限界として示します。"
            ),
            limitations_en=(
                "A convex analytic lesson; the weighted-sum warning describes "
                "the general non-convex limitation."
            ),
        ),
        experiment=VisualizationExperiment(
            oracle_policy=["objective_vector"],
            initial_condition=VisualizationInitialCondition(point=[1.0, 1.0]),
            parameter_preset_id="PRESET_BIOBJECTIVE_GRID",
            seed=VisualizationSeed(status="not_applicable", value=None),
            budget=VisualizationBudget(metric="oracle_evaluations", value=81),
            stopping={"grid_complete": True},
            tuning_policy="fixed_preset",
        ),
        runs=[
            VisualizationRun(
                run_id="RUN_BIOBJECTIVE_GRID",
                method_id="M_NSGA_II",
                profile_id="PROFILE_NSGA_II_PARETO_FRONT",
                implementation_mapping_status="not_applicable",
                implementation_id=None,
                artifact_id=PARETO_ARTIFACT_ID,
            )
        ],
        artifact=VisualizationArtifact(
            artifact_kind="result_visualization",
            artifact_contract="ParetoFront",
            artifact_contract_version="1.1.0",
            renderer_family="pareto_front",
            renderer_contract_version="1.1.0",
            observable_ids=[item.observable_id for item in observables],
            payload_path=path,
            payload_bytes=size,
            payload_sha256=digest,
        ),
        source_ids=["S039", "S055", "S068"],
        last_verified=LAST_VERIFIED,
    )


def _pareto_preference_scenario(
    primary_scenario: VisualizationScenario,
) -> VisualizationScenario:
    """Derive a preference-sensitivity lesson without duplicating its result artifact."""
    payload = primary_scenario.model_dump(mode="python")
    lesson = primary_scenario.lesson.model_dump(mode="python")
    lesson.update(
        {
            "learning_objective": {
                "ja": "同じPareto frontから、weightによって選択点が変わることを読む",
                "en": "Read how weights select different points from the same Pareto front",
            },
            "misconception": {
                "ja": "weightを変えて得た1点が、多目的問題の唯一のbestである",
                "en": "A point selected by one weight is the unique best solution",
            },
            "expected_phenomenon_ja": (
                "非劣候補と解析的frontは固定したまま、f1のweightを0.2、0.5、0.8へ"
                "変えると選択点だけがfront上を移動します。"
            ),
            "expected_phenomenon_en": (
                "The non-dominated candidates and analytic front stay fixed while weights "
                "0.2, 0.5, and 0.8 move only the selected point along the front."
            ),
            "success_signals": [
                {
                    "signal_id": "preference_moves_selection",
                    "label_ja": "weightごとの選択点をfrontと区別できる",
                    "label_en": "distinguishes each weighted selection from the front",
                    "observable_ids": ["pareto_front", "preference_selection"],
                }
            ],
            "failure_signals": [
                {
                    "signal_id": "single_best_misread",
                    "label_ja": "1つのweightによる選択を唯一のbestと誤読する",
                    "label_en": "misreads one weighted selection as the unique best",
                    "observable_ids": ["preference_selection", "ideal_nadir"],
                }
            ],
            "comparison_role": "sensitivity_variant",
            "recommended_next_scenario_ids": [PARETO_SCENARIO_ID],
            "static_summary": {
                "ja": "同じPareto front上で3つのpreference weightによる選択点を比べます。",
                "en": "Compare selections from three preference weights on one Pareto front.",
            },
            "text_alternative": {
                "ja": "weight 0.2、0.5、0.8で、同じ非劣front上の異なる3点を選びます。",
                "en": "Weights 0.2, 0.5, and 0.8 select three different points on one front.",
            },
            "derived_media_caption": {
                "ja": "固定したPareto frontに対するpreference weight感度",
                "en": "Preference-weight sensitivity on a fixed Pareto front",
            },
            "limitations_ja": (
                "解析的な凸front上のweighted-sum選択教材です。一般の非凸frontでは、"
                "weightを走査しても取得できない非劣点があります。"
            ),
            "limitations_en": (
                "A weighted-sum selection lesson on an analytic convex front; scanning "
                "weights can miss non-dominated points on a non-convex front."
            ),
        }
    )
    payload.update(
        {
            "scenario_id": PARETO_PREFERENCE_SCENARIO_ID,
            "identity_status": "derived",
            "canonical_scenario_id": PARETO_SCENARIO_ID,
            "title_ja": "preference weightで選択点がどう動くか比べる",
            "title_en": "Compare how preference weights move the selected point",
            "purpose": "sensitivity",
            "lesson": lesson,
            "last_verified": "2026-07-17",
        }
    )
    return VisualizationScenario.model_validate(payload)


def _canonical_bytes(model: TraceModel, *, canonicalize_floats: bool = False) -> bytes:
    payload = model.model_dump(mode="json")
    if canonicalize_floats:
        payload = _canonicalize_floats(payload)
    payload = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return (payload + "\n").encode("utf-8")


def _canonicalize_floats(value: object) -> object:
    """Remove platform-specific libm noise before hashing the topology trace."""
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


def validate_reference_geometry() -> None:
    """Small explicit guard for the canonical constrained reference."""
    artifact = generate_feasible_region_artifact("validation")
    point = artifact.best_feasible_point
    distance = math.dist(point, artifact.constraint.center)
    if not math.isclose(distance, artifact.constraint.radius, abs_tol=1e-9):
        raise ValueError("known constrained reference is not on the active boundary")
