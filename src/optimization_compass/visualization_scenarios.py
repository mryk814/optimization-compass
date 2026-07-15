from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator

from optimization_compass.trace_models import NonBlank, TraceModel

Purpose = Literal["mechanism", "comparison", "failure_contrast", "sensitivity"]
ArtifactKind = Literal[
    "executable_trace", "schematic_animation", "static_diagram", "result_visualization"
]
RendererFamily = Literal[
    "simplex_geometry",
    "continuous_trajectory",
    "generic_metric_history",
    "search_tree",
    "surrogate_uncertainty",
]
ScenarioIdentityStatus = Literal["canonical", "derived", "generated_only"]

CANONICAL_SCENARIO_IDS = frozenset(
    {
        "SCENARIO_ADAM_QUADRATIC",
        "SCENARIO_GD_QUADRATIC",
        "SCENARIO_MOMENTUM_QUADRATIC",
        "SCENARIO_NM_QUADRATIC",
        "SCENARIO_NM_ROSENBROCK",
    }
)

DERIVED_SCENARIO_BASE_IDS = {
    "SCENARIO_NM_QUADRATIC_SHIFTED": "SCENARIO_NM_QUADRATIC",
    "SCENARIO_NM_ROSENBROCK_SHIFTED": "SCENARIO_NM_ROSENBROCK",
    "SCENARIO_GRADIENT_DESCENT_QUADRATIC": "SCENARIO_GD_QUADRATIC",
    "SCENARIO_GRADIENT_DESCENT_QUADRATIC_DIVERGENCE": "SCENARIO_GD_QUADRATIC",
    "SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE": "SCENARIO_MOMENTUM_QUADRATIC",
    "SCENARIO_ADAM_QUADRATIC_DIVERGENCE": "SCENARIO_ADAM_QUADRATIC",
}


def scenario_identity(scenario_id: str) -> tuple[ScenarioIdentityStatus, str | None]:
    if scenario_id in CANONICAL_SCENARIO_IDS:
        return "canonical", scenario_id
    if scenario_id in DERIVED_SCENARIO_BASE_IDS:
        return "derived", DERIVED_SCENARIO_BASE_IDS[scenario_id]
    return "generated_only", None


ParameterValue = bool | int | float


class VisualizationLesson(TraceModel):
    expected_phenomenon_ja: NonBlank
    expected_phenomenon_en: NonBlank
    limitations_ja: NonBlank
    limitations_en: NonBlank


class VisualizationInitialCondition(TraceModel):
    point: list[float] = Field(min_length=1)


class VisualizationBudget(TraceModel):
    metric: Literal["oracle_evaluations"]
    value: int = Field(gt=0)


class VisualizationSeed(TraceModel):
    status: Literal["fixed", "not_applicable"]
    value: int | None

    @model_validator(mode="after")
    def validate_value(self) -> Self:
        if (self.status == "fixed") != (self.value is not None):
            raise ValueError("fixed seed requires a value; not_applicable requires null")
        return self


class VisualizationExperiment(TraceModel):
    oracle_policy: list[Literal["objective_value", "gradient"]] = Field(min_length=1)
    initial_condition: VisualizationInitialCondition
    parameter_preset_id: NonBlank
    seed: VisualizationSeed
    budget: VisualizationBudget
    stopping: dict[str, ParameterValue]
    tuning_policy: Literal["fixed_preset"]


class VisualizationRun(TraceModel):
    run_id: NonBlank
    method_id: NonBlank
    profile_id: NonBlank
    implementation_mapping_status: Literal["supported", "unsupported", "unknown", "not_applicable"]
    implementation_id: str | None
    artifact_id: NonBlank


class VisualizationArtifact(TraceModel):
    artifact_kind: ArtifactKind
    artifact_contract: Literal["AlgorithmTrace", "SurrogateUncertainty"]
    artifact_contract_version: Literal["1.0.0"]
    renderer_family: RendererFamily
    renderer_contract_version: Literal["1.0.0"]
    observable_ids: list[NonBlank] = Field(min_length=1)
    payload_path: str = Field(pattern=r"^(traces|visualizations)/[a-z0-9._/-]+\.json$")
    payload_bytes: int = Field(gt=0)
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class VisualizationScenario(TraceModel):
    contract_version: Literal["1.0.0"]
    dataset_version: NonBlank
    scenario_id: NonBlank
    identity_status: ScenarioIdentityStatus
    canonical_scenario_id: NonBlank | None
    title_ja: NonBlank
    title_en: NonBlank
    purpose: Purpose
    problem_definition_id: NonBlank
    problem_instance_id: NonBlank
    lesson: VisualizationLesson
    experiment: VisualizationExperiment
    runs: list[VisualizationRun] = Field(min_length=1)
    artifact: VisualizationArtifact
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_unique_ids(self) -> Self:
        if self.identity_status == "canonical" and self.canonical_scenario_id != self.scenario_id:
            raise ValueError("canonical scenarios must point to themselves")
        if self.identity_status == "derived" and self.canonical_scenario_id in {
            None,
            self.scenario_id,
        }:
            raise ValueError("derived scenarios must point to a different canonical scenario")
        if self.identity_status == "generated_only" and self.canonical_scenario_id is not None:
            raise ValueError("generated-only scenarios cannot point to a canonical scenario")
        if len({run.run_id for run in self.runs}) != len(self.runs):
            raise ValueError("run IDs must be unique")
        if len(set(self.artifact.observable_ids)) != len(self.artifact.observable_ids):
            raise ValueError("observable IDs must be unique")
        return self


class VisualizationScenarioIndex(TraceModel):
    contract_version: Literal["1.0.0"]
    dataset_version: NonBlank
    scenarios: list[VisualizationScenario] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_scenarios(self) -> Self:
        if len({scenario.scenario_id for scenario in self.scenarios}) != len(self.scenarios):
            raise ValueError("scenario IDs must be unique")
        if any(scenario.dataset_version != self.dataset_version for scenario in self.scenarios):
            raise ValueError("scenario dataset version must match the index")
        return self
