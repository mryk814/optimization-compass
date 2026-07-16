from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from optimization_compass.content_models import ContentPage
from optimization_compass.visualization_scenarios import (
    VisualizationScenario,
    VisualizationScenarioIndex,
)

JourneyStatus = Literal["complete", "partial", "draft"]
ScenarioRole = Literal["primary", "failure_contrast", "sensitivity", "alternate"]


class JourneyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class JourneyFormulation(JourneyModel):
    variable_domain_summary: str = Field(min_length=1)
    decision_variables: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    constraints: str = Field(min_length=1)


class JourneyScenarioReference(JourneyModel):
    scenario_id: str = Field(min_length=1)
    role: ScenarioRole
    canonical_url: str = Field(pattern=r"^/[A-Za-z0-9._/-]+$")
    problem_definition_id: str = Field(min_length=1)
    problem_instance_id: str = Field(min_length=1)


class JourneyComparisonReference(JourneyModel):
    comparison_id: str = Field(min_length=1)
    canonical_url: str = Field(pattern=r"^/compare/[A-Za-z0-9._-]+$")


class LearningJourney(JourneyModel):
    journey_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    canonical_url: str = Field(pattern=r"^/gallery/[A-Za-z0-9._-]+$")
    title_ja: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    status: JourneyStatus
    completion_reasons: list[str]
    problem_archetype_id: str = Field(min_length=1)
    problem_instance_ids: list[str]
    formulation: JourneyFormulation
    scenarios: list[JourneyScenarioReference]
    comparisons: list[JourneyComparisonReference]
    candidate_method_ids: list[str]
    conditional_method_ids: list[str]
    excluded_method_ids: list[str]
    implementation_ids: list[str]
    content_ids: list[str]
    learning_objective: str = Field(min_length=1)
    prerequisite_journey_ids: list[str]
    takeaway: str = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    last_reviewed: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")

    @model_validator(mode="after")
    def validate_identity_and_lists(self) -> Self:
        if self.journey_id != self.case_id:
            raise ValueError("journey_id must equal its canonical case_id")
        if self.canonical_url != f"/gallery/{self.case_id}":
            raise ValueError("journey canonical_url must be generated from case_id")
        list_fields = (
            "completion_reasons",
            "problem_instance_ids",
            "candidate_method_ids",
            "conditional_method_ids",
            "excluded_method_ids",
            "implementation_ids",
            "content_ids",
            "prerequisite_journey_ids",
            "source_ids",
        )
        for field_name in list_fields:
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must contain unique IDs")
        scenario_ids = [reference.scenario_id for reference in self.scenarios]
        comparison_ids = [reference.comparison_id for reference in self.comparisons]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("journey scenario IDs must be unique")
        if len(comparison_ids) != len(set(comparison_ids)):
            raise ValueError("journey comparison IDs must be unique")
        primary_count = sum(reference.role == "primary" for reference in self.scenarios)
        if primary_count > 1:
            raise ValueError("a journey can have at most one primary scenario")
        if self.status == "complete" and (primary_count != 1 or not self.comparisons):
            raise ValueError("complete journeys require a primary scenario and a comparison")
        if self.status == "draft" and not self.completion_reasons:
            raise ValueError("draft journeys must explain why they are incomplete")
        return self


class LearningJourneyIndex(JourneyModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    journeys: list[LearningJourney] = Field(min_length=1)
    orphan_scenario_ids: list[str]
    orphan_comparison_ids: list[str]

    @field_validator("orphan_scenario_ids", "orphan_comparison_ids")
    @classmethod
    def validate_unique_orphans(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("orphan IDs must be unique")
        return values

    @model_validator(mode="after")
    def validate_index(self) -> Self:
        ids = [journey.journey_id for journey in self.journeys]
        if len(ids) != len(set(ids)):
            raise ValueError("journey IDs must be unique")
        if any(journey.dataset_version != self.dataset_version for journey in self.journeys):
            raise ValueError("journey dataset version must match the index")
        journey_ids = set(ids)
        for journey in self.journeys:
            missing = set(journey.prerequisite_journey_ids) - journey_ids
            if missing:
                raise ValueError(
                    f"journey {journey.journey_id} has missing prerequisites: "
                    + ", ".join(sorted(missing))
                )
        _validate_acyclic_prerequisites(self.journeys)
        return self


def build_learning_journey_index(
    *,
    dataset_version: str,
    generated_at: datetime,
    gallery_index: Mapping[str, Any],
    scenario_index: VisualizationScenarioIndex,
    comparison_index: Mapping[str, Any],
    content_pages: Iterable[ContentPage],
    inventories: Mapping[str, set[str]],
) -> LearningJourneyIndex:
    if gallery_index.get("dataset_version") != dataset_version:
        raise ValueError("gallery dataset version does not match the learning journey index")
    if comparison_index.get("dataset_version") != dataset_version:
        raise ValueError("comparison dataset version does not match the learning journey index")
    if scenario_index.dataset_version != dataset_version:
        raise ValueError("scenario dataset version does not match the learning journey index")

    pages = list(content_pages)
    scenarios_by_id = {scenario.scenario_id: scenario for scenario in scenario_index.scenarios}
    comparisons_by_id = {
        str(comparison["comparison_id"]): comparison
        for comparison in comparison_index.get("comparisons", [])
    }
    journey_rows: list[LearningJourney] = []
    linked_scenarios: set[str] = set()
    linked_comparisons: set[str] = set()
    for case in gallery_index.get("cases", []):
        case_id = str(case["case_id"])
        scenarios = _case_scenarios(case, scenario_index.scenarios)
        primary = _primary_scenario(scenarios)
        scenario_references = [
            JourneyScenarioReference(
                scenario_id=scenario.scenario_id,
                role=_scenario_role(scenario, primary),
                canonical_url=_scenario_route(scenario),
                problem_definition_id=scenario.problem_definition_id,
                problem_instance_id=scenario.problem_instance_id,
            )
            for scenario in scenarios
        ]
        comparison_ids = sorted(map(str, case.get("comparison_ids", [])))
        comparison_references = [
            JourneyComparisonReference(
                comparison_id=comparison_id,
                canonical_url=f"/compare/{comparison_id}",
            )
            for comparison_id in comparison_ids
        ]
        missing: list[str] = []
        if primary is None:
            missing.append("missing_primary_scenario")
        if not comparison_references:
            missing.append("missing_comparison")
        if not case.get("implementation_ids"):
            missing.append("missing_implementation")
        if not case.get("source_ids"):
            missing.append("missing_source")
        status: JourneyStatus = (
            "draft" if case.get("status") == "draft" else "complete" if not missing else "partial"
        )
        if status == "draft" and "case_is_draft" not in missing:
            missing.append("case_is_draft")
        candidate_method_ids = sorted(map(str, case.get("candidate_method_ids", [])))
        conditional_method_ids = sorted(
            str(item["method_id"]) for item in case.get("conditional_methods", [])
        )
        all_learning_method_ids = set(candidate_method_ids) | set(conditional_method_ids)
        content_ids = sorted(
            page.content_id for page in pages if page.method_id in all_learning_method_ids
        )
        feature_values = {
            str(item["feature_id"]): str(item["value"]) for item in case.get("feature_values", [])
        }
        journey_rows.append(
            LearningJourney(
                journey_id=case_id,
                case_id=case_id,
                dataset_version=dataset_version,
                canonical_url=f"/gallery/{case_id}",
                title_ja=str(case["title_ja"]),
                title_en=str(case["title_en"]),
                domain=str(case["domain"]),
                status=status,
                completion_reasons=missing,
                problem_archetype_id=str(case["problem_archetype_id"]),
                problem_instance_ids=sorted(
                    {scenario.problem_instance_id for scenario in scenarios}
                ),
                formulation=JourneyFormulation(
                    variable_domain_summary=feature_values.get(
                        "F_VARIABLE_DOMAIN", "not_explicitly_classified"
                    ),
                    decision_variables=str(case["decision_variables"]),
                    objective=str(case["objective"]),
                    constraints=str(case["constraints"]),
                ),
                scenarios=scenario_references,
                comparisons=comparison_references,
                candidate_method_ids=candidate_method_ids,
                conditional_method_ids=conditional_method_ids,
                excluded_method_ids=sorted(
                    str(item["method_id"]) for item in case.get("excluded_methods", [])
                ),
                implementation_ids=sorted(map(str, case.get("implementation_ids", []))),
                content_ids=content_ids,
                learning_objective=str(case["question"]),
                prerequisite_journey_ids=[],
                takeaway=str(case["practical_notes"]),
                limitations=[
                    "教材上の定式化と固定条件に基づく。実データではscale・noise・計算budgetを再確認する。"
                ],
                source_ids=sorted(map(str, case.get("source_ids", []))),
                last_reviewed=str(case["last_reviewed"]),
            )
        )
        linked_scenarios.update(reference.scenario_id for reference in scenario_references)
        linked_comparisons.update(comparison_ids)

    index = LearningJourneyIndex(
        dataset_version=dataset_version,
        generated_at=generated_at,
        journeys=sorted(journey_rows, key=lambda journey: journey.journey_id),
        orphan_scenario_ids=sorted(set(scenarios_by_id) - linked_scenarios),
        orphan_comparison_ids=sorted(set(comparisons_by_id) - linked_comparisons),
    )
    validate_learning_journey_references(index, inventories=inventories)
    return index


def validate_learning_journey_references(
    index: LearningJourneyIndex,
    *,
    inventories: Mapping[str, set[str]],
) -> None:
    reference_fields: dict[str, Callable[[LearningJourney], list[str]]] = {
        "case": lambda journey: [journey.case_id],
        "problem": lambda journey: [journey.problem_archetype_id],
        "scenario": lambda journey: [item.scenario_id for item in journey.scenarios],
        "comparison": lambda journey: [item.comparison_id for item in journey.comparisons],
        "method": lambda journey: [
            *journey.candidate_method_ids,
            *journey.conditional_method_ids,
            *journey.excluded_method_ids,
        ],
        "implementation": lambda journey: journey.implementation_ids,
        "content": lambda journey: journey.content_ids,
        "source": lambda journey: journey.source_ids,
    }
    for journey in index.journeys:
        for entity_type, getter in reference_fields.items():
            missing = set(getter(journey)) - inventories.get(entity_type, set())
            if missing:
                raise ValueError(
                    f"journey {journey.journey_id} has missing {entity_type} references: "
                    + ", ".join(sorted(missing))
                )


def _case_scenarios(
    case: Mapping[str, Any], scenarios: Iterable[VisualizationScenario]
) -> list[VisualizationScenario]:
    visualization_ids = set(map(str, case.get("visualization_ids", [])))
    matches = [
        scenario
        for scenario in scenarios
        if scenario.scenario_id in visualization_ids
        or any(run.artifact_id in visualization_ids for run in scenario.runs)
    ]
    return sorted(matches, key=lambda scenario: scenario.scenario_id)


def _primary_scenario(
    scenarios: list[VisualizationScenario],
) -> VisualizationScenario | None:
    if not scenarios:
        return None
    purpose_priority = {
        "mechanism": 0,
        "application_result": 1,
        "schematic": 2,
        "failure_contrast": 3,
        "sensitivity": 4,
        "comparison": 5,
    }
    return min(
        scenarios,
        key=lambda scenario: (
            purpose_priority[scenario.purpose],
            scenario.identity_status != "canonical",
            scenario.scenario_id,
        ),
    )


def _scenario_role(
    scenario: VisualizationScenario, primary: VisualizationScenario | None
) -> ScenarioRole:
    if primary is not None and scenario.scenario_id == primary.scenario_id:
        return "primary"
    if scenario.purpose == "failure_contrast":
        return "failure_contrast"
    if scenario.purpose == "sensitivity":
        return "sensitivity"
    return "alternate"


def _scenario_route(scenario: VisualizationScenario) -> str:
    renderer = scenario.artifact.renderer_family
    artifact_id = scenario.runs[0].artifact_id
    if renderer == "search_tree":
        return f"/theater/search-tree/{artifact_id}"
    if renderer == "surrogate_uncertainty":
        return f"/theater/bayesian-optimization/{scenario.scenario_id}"
    if renderer == "simplex_geometry":
        return "/theater/nelder-mead"
    if renderer in {"feasible_region", "pareto_front"}:
        return f"/theater/learning/{scenario.scenario_id}"
    return f"/traces/{artifact_id}"


def _validate_acyclic_prerequisites(journeys: list[LearningJourney]) -> None:
    graph = {journey.journey_id: set(journey.prerequisite_journey_ids) for journey in journeys}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(journey_id: str) -> None:
        if journey_id in visiting:
            raise ValueError(f"circular journey prerequisite: {journey_id}")
        if journey_id in visited:
            return
        visiting.add(journey_id)
        for prerequisite_id in graph[journey_id]:
            visit(prerequisite_id)
        visiting.remove(journey_id)
        visited.add(journey_id)

    for journey_id in sorted(graph):
        visit(journey_id)
