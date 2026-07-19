from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator

from optimization_compass.trace_models import NonBlank, TraceModel

Purpose = Literal[
    "mechanism", "comparison", "failure_contrast", "sensitivity", "application_result"
]
ComparisonRole = Literal["primary_example", "sensitivity_variant", "failure_contrast", "baseline"]
KnownReferenceDisplayPolicy = Literal["show", "show_if_available", "not_shown"]
NarrationMilestoneId = Literal["start", "first_change", "pattern_visible", "termination"]
ArtifactKind = Literal[
    "executable_trace", "schematic_animation", "static_diagram", "result_visualization"
]
RendererFamily = Literal[
    "simplex_geometry",
    "continuous_trajectory",
    "generic_metric_history",
    "search_tree",
    "surrogate_uncertainty",
    "feasible_region",
    "pareto_front",
    "field_evolution",
]
ScenarioIdentityStatus = Literal["canonical", "derived", "generated_only"]

CANONICAL_SCENARIO_IDS = frozenset(
    {
        "SCENARIO_ADAM_QUADRATIC",
        "SCENARIO_GD_QUADRATIC",
        "SCENARIO_MOMENTUM_QUADRATIC",
        "SCENARIO_NM_QUADRATIC",
        "SCENARIO_NM_ROSENBROCK",
        "SCENARIO_CONSTRAINED_DISK",
        "SCENARIO_BIOBJECTIVE_QUADRATIC",
        "SCENARIO_TOPOLOGY_SIMP_OC",
    }
)

DERIVED_SCENARIO_BASE_IDS = {
    "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY": "SCENARIO_BIOBJECTIVE_QUADRATIC",
    "SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH": "SCENARIO_CONSTRAINED_DISK",
    "SCENARIO_NM_QUADRATIC_SHIFTED": "SCENARIO_NM_QUADRATIC",
    "SCENARIO_NM_ROSENBROCK_SHIFTED": "SCENARIO_NM_ROSENBROCK",
    "SCENARIO_GRADIENT_DESCENT_QUADRATIC": "SCENARIO_GD_QUADRATIC",
    "SCENARIO_GRADIENT_DESCENT_QUADRATIC_DIVERGENCE": "SCENARIO_GD_QUADRATIC",
    "SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE": "SCENARIO_MOMENTUM_QUADRATIC",
    "SCENARIO_ADAM_QUADRATIC_DIVERGENCE": "SCENARIO_ADAM_QUADRATIC",
    "SCENARIO_TOPOLOGY_CHECKERBOARD": "SCENARIO_TOPOLOGY_SIMP_OC",
    "SCENARIO_TOPOLOGY_OC_MMA_COMPARISON": "SCENARIO_TOPOLOGY_SIMP_OC",
}


def scenario_identity(scenario_id: str) -> tuple[ScenarioIdentityStatus, str | None]:
    if scenario_id in CANONICAL_SCENARIO_IDS:
        return "canonical", scenario_id
    if scenario_id in DERIVED_SCENARIO_BASE_IDS:
        return "derived", DERIVED_SCENARIO_BASE_IDS[scenario_id]
    return "generated_only", None


ParameterValue = bool | int | float
GuidedPlaybackSpeed = float


class LocalizedText(TraceModel):
    ja: NonBlank
    en: NonBlank


class VisualizationObservable(TraceModel):
    observable_id: NonBlank
    label_ja: NonBlank
    label_en: NonBlank


class VisualizationSignal(TraceModel):
    signal_id: NonBlank
    label_ja: NonBlank
    label_en: NonBlank
    observable_ids: list[NonBlank] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_observables(self) -> Self:
        if len(set(self.observable_ids)) != len(self.observable_ids):
            raise ValueError("signal observable IDs must be unique")
        return self


class VisualizationNarrationStep(TraceModel):
    milestone_id: NarrationMilestoneId
    title_ja: NonBlank
    title_en: NonBlank
    observable_ids: list[NonBlank] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_observables(self) -> Self:
        if len(set(self.observable_ids)) != len(self.observable_ids):
            raise ValueError("narration observable IDs must be unique")
        return self


class GuidedStoryStep(TraceModel):
    milestone_id: NarrationMilestoneId
    annotation: LocalizedText
    frame_index: int = Field(ge=0)
    auto_pause: bool
    focus_target: NonBlank
    viewport_preset: NonBlank
    camera_preset: NonBlank | None
    playback_speed: GuidedPlaybackSpeed
    visible_layers: list[NonBlank] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_layers(self) -> Self:
        if self.playback_speed not in {0.25, 0.5, 1.0, 2.0, 4.0}:
            raise ValueError("guided story playback speed is unsupported")
        if len(set(self.visible_layers)) != len(self.visible_layers):
            raise ValueError("guided story visible layers must be unique")
        return self


class GuidedStory(TraceModel):
    story_version: Literal["1.0.0"]
    introduction: LocalizedText
    steps: list[GuidedStoryStep] = Field(min_length=3)
    summary: LocalizedText

    @model_validator(mode="after")
    def validate_steps(self) -> Self:
        milestones = [step.milestone_id for step in self.steps]
        if len(set(milestones)) != len(milestones):
            raise ValueError("guided story milestone IDs must be unique")
        if milestones[0] != "start" or milestones[-1] != "termination":
            raise ValueError("guided story must start at start and end at termination")
        return self


class KnownReferenceDisplay(TraceModel):
    policy: KnownReferenceDisplayPolicy
    note_ja: NonBlank
    note_en: NonBlank


class VisualizationLesson(TraceModel):
    learning_objective: LocalizedText
    misconception: LocalizedText | None
    expected_phenomenon_ja: NonBlank
    expected_phenomenon_en: NonBlank
    success_signals: list[VisualizationSignal] = Field(min_length=1)
    failure_signals: list[VisualizationSignal]
    primary_observables: list[VisualizationObservable] = Field(min_length=1)
    secondary_observables: list[VisualizationObservable]
    narration_steps: list[VisualizationNarrationStep] = Field(min_length=3)
    comparison_role: ComparisonRole
    prerequisite_concept_ids: list[NonBlank]
    recommended_next_scenario_ids: list[NonBlank]
    known_reference_display: KnownReferenceDisplay
    static_summary: LocalizedText
    text_alternative: LocalizedText
    derived_media_caption: LocalizedText
    limitations_ja: NonBlank
    limitations_en: NonBlank

    @model_validator(mode="after")
    def validate_unique_ids(self) -> Self:
        signal_ids = [signal.signal_id for signal in [*self.success_signals, *self.failure_signals]]
        if len(set(signal_ids)) != len(signal_ids):
            raise ValueError("lesson signal IDs must be unique")
        for label, values in (
            ("prerequisite concept", self.prerequisite_concept_ids),
            ("recommended scenario", self.recommended_next_scenario_ids),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{label} IDs must be unique")
        return self


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
    oracle_policy: list[
        Literal[
            "objective_value",
            "gradient",
            "constraint_value",
            "constraint_jacobian",
            "objective_vector",
            "residual_vector",
            "jacobian",
        ]
    ] = Field(min_length=1)
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
    artifact_contract: Literal[
        "AlgorithmTrace",
        "SurrogateUncertainty",
        "FeasibleRegion",
        "ParetoFront",
        "TopologyFieldEvolution",
    ]
    artifact_contract_version: Literal["1.0.0", "1.1.0"]
    renderer_family: RendererFamily
    renderer_contract_version: Literal["1.0.0", "1.1.0"]
    observable_ids: list[NonBlank] = Field(min_length=1)
    payload_path: str = Field(pattern=r"^(traces|visualizations)/[a-z0-9._/-]+\.json$")
    payload_bytes: int = Field(gt=0)
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class VisualizationScenario(TraceModel):
    contract_version: Literal["1.2.0"]
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
    guided_story: GuidedStory | None = None
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
        lesson_observables = [
            *self.lesson.primary_observables,
            *self.lesson.secondary_observables,
        ]
        lesson_observable_ids = [item.observable_id for item in lesson_observables]
        if len(set(lesson_observable_ids)) != len(lesson_observable_ids):
            raise ValueError("lesson observable IDs must be unique")
        if not set(lesson_observable_ids).issubset(self.artifact.observable_ids):
            raise ValueError("lesson observables must be provided by the artifact")
        signal_observable_ids = {
            observable_id
            for signal in [*self.lesson.success_signals, *self.lesson.failure_signals]
            for observable_id in signal.observable_ids
        }
        if not signal_observable_ids.issubset(lesson_observable_ids):
            raise ValueError("signal observables must be declared by the lesson")
        milestone_ids = [step.milestone_id for step in self.lesson.narration_steps]
        if len(set(milestone_ids)) != len(milestone_ids):
            raise ValueError("narration milestone IDs must be unique")
        if milestone_ids[0] != "start" or milestone_ids[-1] != "termination":
            raise ValueError("narration must start at start and end at termination")
        if any(
            not set(step.observable_ids).issubset(lesson_observable_ids)
            for step in self.lesson.narration_steps
        ):
            raise ValueError("narration observables must be declared by the lesson")
        if self.guided_story is not None:
            narration_ids = set(milestone_ids)
            artifact_observables = set(self.artifact.observable_ids)
            for step in self.guided_story.steps:
                if step.milestone_id not in narration_ids:
                    raise ValueError("guided story milestones must be declared by the lesson")
                if step.focus_target not in artifact_observables:
                    raise ValueError("guided story focus target must be an artifact observable")
                if not set(step.visible_layers).issubset(artifact_observables):
                    raise ValueError("guided story layers must be artifact observables")
        if self.purpose in {"failure_contrast", "sensitivity"} and (
            self.lesson.misconception is None or not self.lesson.failure_signals
        ):
            raise ValueError(
                "failure and sensitivity scenarios require a misconception and failure signals"
            )
        return self


class VisualizationScenarioIndex(TraceModel):
    contract_version: Literal["1.2.0"]
    dataset_version: NonBlank
    scenarios: list[VisualizationScenario] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_scenarios(self) -> Self:
        if len({scenario.scenario_id for scenario in self.scenarios}) != len(self.scenarios):
            raise ValueError("scenario IDs must be unique")
        if any(scenario.dataset_version != self.dataset_version for scenario in self.scenarios):
            raise ValueError("scenario dataset version must match the index")
        scenario_ids = {scenario.scenario_id for scenario in self.scenarios}
        recommended_ids = {
            recommended_id
            for scenario in self.scenarios
            for recommended_id in scenario.lesson.recommended_next_scenario_ids
        }
        if not recommended_ids.issubset(scenario_ids):
            raise ValueError("recommended scenarios must exist in the index")
        return self
