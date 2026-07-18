from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from datetime import date, datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from optimization_compass.content_markdown import render_inline_markdown
from optimization_compass.content_models import ContentPage
from optimization_compass.evidence import (
    EXPECTED_CURRENTNESS_BY_SOURCE_TYPE,
    SOURCE_FRESHNESS_DAYS,
    SourceEvidenceIndex,
)
from optimization_compass.learning_journey_policy import LearningJourneyAssetPolicyIndex
from optimization_compass.visualization_scenarios import (
    VisualizationScenario,
    VisualizationScenarioIndex,
)

JourneyStatus = Literal["complete", "partial", "draft"]
ScenarioRole = Literal["primary", "failure_contrast", "sensitivity", "alternate"]
JourneyDimensionState = Literal["complete", "missing", "not_applicable", "broken"]
JourneyOrphanPolicy = Literal["standalone", "warning", "error"]

JOURNEY_DIMENSIONS = (
    "formulation",
    "canonical_problem_instance",
    "primary_scenario",
    "alternate_scenario",
    "canonical_comparison",
    "method_roles",
    "implementation",
    "source_review",
    "terminology_prerequisite",
    "static_text_alternative",
    "cross_surface_links",
    "route_reachability",
    "validation_status",
)


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
    limitations: list[str]
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
        if self.status == "complete":
            if primary_count != 1 or not self.comparisons:
                raise ValueError("complete journeys require a primary scenario and a comparison")
            if self.completion_reasons:
                raise ValueError("complete journeys cannot have completion reasons")
        elif not self.completion_reasons:
            raise ValueError("incomplete journeys must explain why they are incomplete")
        return self


class JourneyCompletenessDimension(JourneyModel):
    state: JourneyDimensionState
    target_ids: list[str]
    reason_codes: list[str]

    @model_validator(mode="after")
    def validate_state_and_reasons(self) -> Self:
        if len(self.target_ids) != len(set(self.target_ids)):
            raise ValueError("dimension target IDs must be unique")
        if len(self.reason_codes) != len(set(self.reason_codes)):
            raise ValueError("dimension reason codes must be unique")
        if self.state == "complete" and self.reason_codes:
            raise ValueError("complete dimensions cannot have reason codes")
        if self.state in {"missing", "broken"} and not self.reason_codes:
            raise ValueError("missing and broken dimensions require reason codes")
        return self


class JourneyCompletenessAssessment(JourneyModel):
    journey_id: str = Field(min_length=1)
    status: JourneyStatus
    dimensions: dict[str, JourneyCompletenessDimension]
    missing_dimensions: list[str]

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        if set(self.dimensions) != set(JOURNEY_DIMENSIONS):
            raise ValueError("journey completeness dimensions must match the contract")
        expected_missing = sorted(
            name
            for name, dimension in self.dimensions.items()
            if dimension.state in {"missing", "broken"}
        )
        if self.missing_dimensions != expected_missing:
            raise ValueError("missing_dimensions must be derived from dimension states")
        if self.status == "complete" and self.missing_dimensions:
            raise ValueError("complete journey assessment cannot have missing dimensions")
        if self.status == "partial" and not self.missing_dimensions:
            raise ValueError("partial journey assessment requires missing dimensions")
        return self


class JourneyCompletenessSummary(JourneyModel):
    target_complete_journeys: Literal[5] = 5
    total_journeys: int = Field(ge=0)
    status_counts: dict[str, int]
    milestone_status: Literal["met", "not_met"]

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        if set(self.status_counts) != {"complete", "partial", "draft"}:
            raise ValueError("journey status counts must be explicit")
        if any(count < 0 for count in self.status_counts.values()):
            raise ValueError("journey status counts cannot be negative")
        if sum(self.status_counts.values()) != self.total_journeys:
            raise ValueError("journey status counts must equal total_journeys")
        expected = (
            "met" if self.status_counts["complete"] >= self.target_complete_journeys else "not_met"
        )
        if self.milestone_status != expected:
            raise ValueError("journey milestone status must be derived from complete count")
        return self


class JourneyOrphanAsset(JourneyModel):
    asset_type: Literal["scenario", "comparison", "visualization_artifact", "content"]
    asset_id: str = Field(min_length=1)
    policy: JourneyOrphanPolicy
    reason_code: str = Field(min_length=1)


class LearningJourneyIndex(JourneyModel):
    contract_version: Literal["1.1.0"] = "1.1.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    summary: JourneyCompletenessSummary
    journeys: list[LearningJourney] = Field(min_length=1)
    assessments: list[JourneyCompletenessAssessment] = Field(min_length=1)
    orphan_assets: list[JourneyOrphanAsset]

    @model_validator(mode="after")
    def validate_index(self) -> Self:
        ids = [journey.journey_id for journey in self.journeys]
        if len(ids) != len(set(ids)):
            raise ValueError("journey IDs must be unique")
        if any(journey.dataset_version != self.dataset_version for journey in self.journeys):
            raise ValueError("journey dataset version must match the index")
        assessment_ids = [assessment.journey_id for assessment in self.assessments]
        if len(assessment_ids) != len(set(assessment_ids)):
            raise ValueError("journey assessment IDs must be unique")
        if set(assessment_ids) != set(ids):
            raise ValueError("every journey must have exactly one completeness assessment")
        assessment_by_id = {assessment.journey_id: assessment for assessment in self.assessments}
        for journey in self.journeys:
            assessment = assessment_by_id[journey.journey_id]
            if assessment.status != journey.status:
                raise ValueError("journey and assessment status must match")
            expected_reasons = sorted(
                {
                    reason
                    for dimension in assessment.dimensions.values()
                    for reason in dimension.reason_codes
                }
                | ({"case_is_draft"} if journey.status == "draft" else set())
            )
            if journey.completion_reasons != expected_reasons:
                raise ValueError("journey completion reasons must match its assessment")
        counts = Counter(journey.status for journey in self.journeys)
        if self.summary.total_journeys != len(self.journeys) or any(
            self.summary.status_counts[status] != counts.get(status, 0)
            for status in ("complete", "partial", "draft")
        ):
            raise ValueError("journey summary must be derived from journeys")
        if len({(item.asset_type, item.asset_id) for item in self.orphan_assets}) != len(
            self.orphan_assets
        ):
            raise ValueError("orphan assets must be unique")
        if any(item.policy == "error" for item in self.orphan_assets):
            raise ValueError("error-policy orphan assets cannot be published")
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
    source_index: SourceEvidenceIndex,
    asset_policy: LearningJourneyAssetPolicyIndex,
    inventories: Mapping[str, set[str]],
) -> LearningJourneyIndex:
    if gallery_index.get("dataset_version") != dataset_version:
        raise ValueError("gallery dataset version does not match the learning journey index")
    if comparison_index.get("dataset_version") != dataset_version:
        raise ValueError("comparison dataset version does not match the learning journey index")
    if scenario_index.dataset_version != dataset_version:
        raise ValueError("scenario dataset version does not match the learning journey index")
    if source_index.dataset_version != dataset_version:
        raise ValueError("source dataset version does not match the learning journey index")

    pages = list(content_pages)
    scenarios_by_id = {scenario.scenario_id: scenario for scenario in scenario_index.scenarios}
    comparisons_by_id = {
        str(comparison["comparison_id"]): comparison
        for comparison in comparison_index.get("comparisons", [])
    }
    cases_by_id = {str(case["case_id"]): case for case in gallery_index.get("cases", [])}
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
        candidate_method_ids = sorted(
            str(item["method_id"]) for item in case.get("candidate_methods", [])
        )
        conditional_method_ids = sorted(
            str(item["method_id"]) for item in case.get("conditional_methods", [])
        )
        all_learning_method_ids = set(candidate_method_ids) | set(conditional_method_ids)
        content_ids = sorted(
            page.content_id for page in pages if page.method_id in all_learning_method_ids
        )
        linked_pages = [page for page in pages if page.content_id in content_ids]
        journey_source_ids = sorted(
            {
                *map(str, case.get("source_ids", [])),
                *(str(source_id) for scenario in scenarios for source_id in scenario.source_ids),
                *(
                    str(source_id)
                    for comparison_id in comparison_ids
                    for source_id in comparisons_by_id.get(comparison_id, {}).get("source_ids", [])
                ),
                *(str(source_id) for page in linked_pages for source_id in page.source_ids),
            }
        )
        journey_rows.append(
            LearningJourney(
                journey_id=case_id,
                case_id=case_id,
                dataset_version=dataset_version,
                canonical_url=f"/gallery/{case_id}",
                title_ja=str(case["title_ja"]),
                title_en=str(case["title_en"]),
                domain=str(case["domain"]),
                status="draft" if case.get("status") == "draft" else "partial",
                completion_reasons=["case_is_draft"]
                if case.get("status") == "draft"
                else ["pending_completeness_assessment"],
                problem_archetype_id=str(case["problem_archetype_id"]),
                problem_instance_ids=sorted(
                    {scenario.problem_instance_id for scenario in scenarios}
                ),
                formulation=JourneyFormulation(
                    variable_domain_summary=render_inline_markdown(str(case["variable_domain"])),
                    decision_variables=render_inline_markdown(str(case["decision_variables"])),
                    objective=render_inline_markdown(str(case["objective"])),
                    constraints=render_inline_markdown(str(case["constraints"])),
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
                limitations=sorted(map(str, case.get("limitations", []))),
                source_ids=journey_source_ids,
                last_reviewed=str(case["last_reviewed"]),
            )
        )
        linked_scenarios.update(reference.scenario_id for reference in scenario_references)
        linked_comparisons.update(comparison_ids)

    assessed_rows: list[LearningJourney] = []
    assessments: list[JourneyCompletenessAssessment] = []
    for journey in journey_rows:
        assessed, assessment = _assess_journey(
            journey,
            case_is_draft=journey.status == "draft",
            case=cases_by_id[journey.case_id],
            scenarios_by_id=scenarios_by_id,
            comparisons_by_id=comparisons_by_id,
            content_pages=pages,
            source_index=source_index,
            inventories=inventories,
            generated_at=generated_at,
        )
        assessed_rows.append(assessed)
        assessments.append(assessment)

    counts = Counter(journey.status for journey in assessed_rows)
    complete_count = counts.get("complete", 0)
    orphan_assets = _classify_orphan_assets(
        scenario_index=scenario_index,
        comparison_index=comparison_index,
        linked_scenarios=linked_scenarios,
        linked_comparisons=linked_comparisons,
        content_pages=pages,
        linked_content={item for journey in assessed_rows for item in journey.content_ids},
        asset_policy=asset_policy,
    )
    _reject_error_orphans(orphan_assets)
    index = LearningJourneyIndex(
        dataset_version=dataset_version,
        generated_at=generated_at,
        summary=JourneyCompletenessSummary(
            total_journeys=len(assessed_rows),
            status_counts={
                status: counts.get(status, 0) for status in ("complete", "partial", "draft")
            },
            milestone_status="met" if complete_count >= 5 else "not_met",
        ),
        journeys=sorted(assessed_rows, key=lambda journey: journey.journey_id),
        assessments=sorted(assessments, key=lambda assessment: assessment.journey_id),
        orphan_assets=orphan_assets,
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


def _assess_journey(
    journey: LearningJourney,
    *,
    case_is_draft: bool,
    case: Mapping[str, Any],
    scenarios_by_id: Mapping[str, VisualizationScenario],
    comparisons_by_id: Mapping[str, Mapping[str, Any]],
    content_pages: list[ContentPage],
    source_index: SourceEvidenceIndex,
    inventories: Mapping[str, set[str]],
    generated_at: datetime,
) -> tuple[LearningJourney, JourneyCompletenessAssessment]:
    primary = [item for item in journey.scenarios if item.role == "primary"]
    diagnostic_scenarios = [
        item for item in journey.scenarios if item.role in {"failure_contrast", "sensitivity"}
    ]
    reference_issues = _missing_journey_references(journey, inventories=inventories)
    routes = [
        journey.canonical_url,
        *(item.canonical_url for item in journey.scenarios),
        *(item.canonical_url for item in journey.comparisons),
        *(
            f"/methods/{method_id}"
            for method_id in sorted(
                {
                    *journey.candidate_method_ids,
                    *journey.conditional_method_ids,
                    *journey.excluded_method_ids,
                }
            )
        ),
        *(f"/sources/{source_id}" for source_id in journey.source_ids),
    ]
    scenario_ids = [item.scenario_id for item in journey.scenarios]
    has_static_alternatives = bool(scenario_ids) and all(
        scenario_id in scenarios_by_id
        and scenarios_by_id[scenario_id].lesson.static_summary.ja.strip()
        and scenarios_by_id[scenario_id].lesson.text_alternative.ja.strip()
        for scenario_id in scenario_ids
    )
    comparison_issues = _comparison_issues(journey, comparisons_by_id=comparisons_by_id)
    method_role_issues = _method_role_issues(journey, case=case)
    pages_by_id = {page.content_id: page for page in content_pages}
    represented_method_ids = {
        pages_by_id[content_id].method_id
        for content_id in journey.content_ids
        if content_id in pages_by_id and pages_by_id[content_id].status == "published"
    }
    expected_method_ids = {
        *journey.candidate_method_ids,
        *journey.conditional_method_ids,
    }
    terminology_complete = bool(expected_method_ids) and expected_method_ids.issubset(
        represented_method_ids
    )
    source_review_issues = _source_review_issues(
        journey,
        case=case,
        scenarios_by_id=scenarios_by_id,
        comparisons_by_id=comparisons_by_id,
        content_pages=content_pages,
        source_index=source_index,
        generated_at=generated_at,
    )
    broken_routes = sorted(
        route
        for route in routes
        if not _route_is_reachable(
            route,
            journey=journey,
            scenarios_by_id=scenarios_by_id,
            comparisons_by_id=comparisons_by_id,
            inventories=inventories,
        )
    )
    dimensions = {
        "formulation": _dimension(
            bool(
                journey.formulation.variable_domain_summary != "not_explicitly_classified"
                and journey.formulation.decision_variables
                and journey.formulation.objective
                and journey.formulation.constraints
            ),
            [journey.case_id],
            "missing_formulation",
        ),
        "canonical_problem_instance": _dimension(
            bool(journey.problem_instance_ids),
            journey.problem_instance_ids,
            "missing_problem_instance",
        ),
        "primary_scenario": _dimension(
            len(primary) == 1,
            [item.scenario_id for item in primary],
            "missing_primary_scenario",
        ),
        "alternate_scenario": _dimension(
            bool(diagnostic_scenarios),
            [item.scenario_id for item in diagnostic_scenarios],
            "missing_failure_or_sensitivity_scenario",
        ),
        "canonical_comparison": _dimension_with_reasons(
            not comparison_issues,
            [item.comparison_id for item in journey.comparisons],
            comparison_issues or ["missing_comparison"],
        ),
        "method_roles": _dimension_with_reasons(
            not method_role_issues,
            sorted(
                {
                    *journey.candidate_method_ids,
                    *journey.conditional_method_ids,
                    *journey.excluded_method_ids,
                }
            ),
            method_role_issues or ["missing_method_role"],
        ),
        "implementation": _dimension(
            bool(journey.implementation_ids),
            journey.implementation_ids,
            "missing_implementation",
        ),
        "source_review": _dimension_with_reasons(
            not source_review_issues,
            journey.source_ids,
            source_review_issues or ["missing_source_review"],
        ),
        "terminology_prerequisite": _dimension(
            terminology_complete,
            journey.content_ids,
            "missing_terminology_prerequisite",
        ),
        "static_text_alternative": _dimension_with_reasons(
            has_static_alternatives and bool(journey.limitations),
            scenario_ids,
            [
                *([] if has_static_alternatives else ["missing_static_text_alternative"]),
                *([] if journey.limitations else ["missing_limitations"]),
            ],
        ),
        "cross_surface_links": _dimension(
            bool(primary and journey.comparisons and journey.candidate_method_ids),
            routes,
            "missing_cross_surface_link",
        ),
        "route_reachability": JourneyCompletenessDimension(
            state="broken" if broken_routes else "complete",
            target_ids=routes,
            reason_codes=["broken_route"] if broken_routes else [],
        ),
        "validation_status": JourneyCompletenessDimension(
            state="broken" if reference_issues else "complete",
            target_ids=sorted(
                f"{entity_type}:{entity_id}"
                for entity_type, entity_ids in reference_issues.items()
                for entity_id in entity_ids
            ),
            reason_codes=["broken_reference"] if reference_issues else [],
        ),
    }
    missing_dimensions = sorted(
        name for name, dimension in dimensions.items() if dimension.state in {"missing", "broken"}
    )
    non_route_missing = [
        name
        for name in missing_dimensions
        if name not in {"route_reachability", "validation_status"}
    ]
    _reject_broken_routes_for_otherwise_complete_journey(
        journey_id=journey.journey_id,
        broken_routes=broken_routes,
        non_route_missing=non_route_missing,
        reference_issues=reference_issues,
    )
    status: JourneyStatus = (
        "draft" if case_is_draft else "partial" if missing_dimensions else "complete"
    )
    completion_reasons = sorted(
        {reason for dimension in dimensions.values() for reason in dimension.reason_codes}
        | ({"case_is_draft"} if case_is_draft else set())
    )
    assessed = LearningJourney.model_validate(
        {
            **journey.model_dump(mode="python"),
            "status": status,
            "completion_reasons": completion_reasons,
        }
    )
    return assessed, JourneyCompletenessAssessment(
        journey_id=journey.journey_id,
        status=status,
        dimensions=dimensions,
        missing_dimensions=missing_dimensions,
    )


def _reject_broken_routes_for_otherwise_complete_journey(
    *,
    journey_id: str,
    broken_routes: list[str],
    non_route_missing: list[str],
    reference_issues: Mapping[str, list[str]],
) -> None:
    if broken_routes and not non_route_missing and not reference_issues:
        raise ValueError(
            f"public complete journey {journey_id} has broken routes: " + ", ".join(broken_routes)
        )


def _reject_error_orphans(orphan_assets: list[JourneyOrphanAsset]) -> None:
    blocking_orphans = [item for item in orphan_assets if item.policy == "error"]
    if blocking_orphans:
        raise ValueError(
            "learning journey orphan policy rejected public assets: "
            + ", ".join(f"{item.asset_type}:{item.asset_id}" for item in blocking_orphans)
        )


def _dimension(
    complete: bool,
    target_ids: list[str],
    missing_reason: str,
    *,
    broken: bool = False,
) -> JourneyCompletenessDimension:
    return JourneyCompletenessDimension(
        state="complete" if complete else "broken" if broken else "missing",
        target_ids=target_ids,
        reason_codes=[] if complete else [missing_reason],
    )


def _dimension_with_reasons(
    complete: bool,
    target_ids: list[str],
    missing_reasons: list[str],
) -> JourneyCompletenessDimension:
    return JourneyCompletenessDimension(
        state="complete" if complete else "missing",
        target_ids=target_ids,
        reason_codes=[] if complete else sorted(set(missing_reasons)),
    )


def _missing_journey_references(
    journey: LearningJourney,
    *,
    inventories: Mapping[str, set[str]],
) -> dict[str, list[str]]:
    reference_fields: dict[str, list[str]] = {
        "case": [journey.case_id],
        "problem": [journey.problem_archetype_id],
        "scenario": [item.scenario_id for item in journey.scenarios],
        "comparison": [item.comparison_id for item in journey.comparisons],
        "method": [
            *journey.candidate_method_ids,
            *journey.conditional_method_ids,
            *journey.excluded_method_ids,
        ],
        "implementation": journey.implementation_ids,
        "content": journey.content_ids,
        "source": journey.source_ids,
    }
    return {
        entity_type: sorted(set(ids) - inventories.get(entity_type, set()))
        for entity_type, ids in reference_fields.items()
        if set(ids) - inventories.get(entity_type, set())
    }


def _comparison_issues(
    journey: LearningJourney,
    *,
    comparisons_by_id: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    if not journey.comparisons:
        return ["missing_comparison"]
    issues: set[str] = set()
    required_fields = (
        "fixed_factors",
        "changed_factors",
        "budget",
        "metrics",
        "fairness_note",
        "caveat",
        "limitations",
        "members",
    )
    for reference in journey.comparisons:
        comparison = comparisons_by_id.get(reference.comparison_id)
        if comparison is None:
            issues.add("broken_comparison_reference")
            continue
        if (
            comparison.get("identity_status") != "canonical"
            or comparison.get("canonical_comparison_id") != reference.comparison_id
        ):
            issues.add("comparison_not_canonical")
        if (
            comparison.get("case_id") != journey.case_id
            or comparison.get("journey_id") != journey.journey_id
        ):
            issues.add("comparison_wrong_journey")
        if any(not comparison.get(field) for field in required_fields):
            issues.add("comparison_contract_incomplete")
    return sorted(issues)


def _method_role_issues(
    journey: LearningJourney,
    *,
    case: Mapping[str, Any],
) -> list[str]:
    issues: set[str] = set()
    candidates = list(case.get("candidate_methods", []))
    if not candidates:
        issues.add("missing_candidate_method")
    conditional = list(case.get("conditional_methods", []))
    excluded = list(case.get("excluded_methods", []))
    if not conditional:
        issues.add("missing_conditional_method")
    if not excluded:
        issues.add("missing_excluded_method")
    if any(
        not str(item.get("reason", "")).strip() for item in [*candidates, *conditional, *excluded]
    ):
        issues.add("missing_method_role_reason")
    return sorted(issues)


def _source_review_issues(
    journey: LearningJourney,
    *,
    case: Mapping[str, Any],
    scenarios_by_id: Mapping[str, VisualizationScenario],
    comparisons_by_id: Mapping[str, Mapping[str, Any]],
    content_pages: list[ContentPage],
    source_index: SourceEvidenceIndex,
    generated_at: datetime,
) -> list[str]:
    issues: set[str] = set()
    source_records = {source.source_id: source for source in source_index.sources}
    surfaces: list[tuple[str, set[str]]] = [
        ("case", set(map(str, case.get("source_ids", [])))),
        *(
            (
                "scenario",
                set(map(str, scenarios_by_id[reference.scenario_id].source_ids)),
            )
            for reference in journey.scenarios
            if reference.scenario_id in scenarios_by_id
        ),
        *(
            (
                "comparison",
                set(
                    map(
                        str,
                        comparisons_by_id.get(reference.comparison_id, {}).get("source_ids", []),
                    )
                ),
            )
            for reference in journey.comparisons
        ),
        *(
            ("content", set(map(str, page.source_ids)))
            for page in content_pages
            if page.status == "published" and page.content_id in journey.content_ids
        ),
    ]
    required_surface_types = {"case", "scenario", "comparison", "content"}
    present_surface_types = {surface_type for surface_type, _ in surfaces}
    for surface_type in sorted(required_surface_types - present_surface_types):
        issues.add(f"missing_{surface_type}_source")
    for surface_type, source_ids in surfaces:
        if not source_ids:
            issues.add(f"missing_{surface_type}_source")
            continue
        resolved = [
            source_records[source_id] for source_id in source_ids if source_id in source_records
        ]
        if len(resolved) != len(source_ids):
            issues.add("unknown_source")
        if resolved and not any(
            source.source_quality in {"high", "primary"} for source in resolved
        ):
            issues.add("weak_source_set")

    for source_id in journey.source_ids:
        source = source_records.get(source_id)
        if source is None:
            issues.add("unknown_source")
            continue
        age_days = (generated_at.date() - source.last_verified).days
        if age_days < 0:
            issues.add("source_verified_in_future")
        elif age_days > SOURCE_FRESHNESS_DAYS[source.source_type]:
            issues.add("stale_source")
        if source.currentness_status != EXPECTED_CURRENTNESS_BY_SOURCE_TYPE[source.source_type]:
            issues.add("invalid_source_currentness")
        if not source.supported_claim.strip():
            issues.add("missing_supported_claim")

    try:
        case_review_age = generated_at.date() - date.fromisoformat(journey.last_reviewed)
        if case_review_age.days < 0 or case_review_age.days > 365:
            issues.add("stale_case_review")
    except ValueError:
        issues.add("stale_case_review")
    return sorted(issues)


def _route_is_reachable(
    route: str,
    *,
    journey: LearningJourney,
    scenarios_by_id: Mapping[str, VisualizationScenario],
    comparisons_by_id: Mapping[str, Mapping[str, Any]],
    inventories: Mapping[str, set[str]],
) -> bool:
    reachable = {journey.canonical_url}
    for reference in journey.scenarios:
        scenario = scenarios_by_id.get(reference.scenario_id)
        if scenario is not None:
            reachable.add(_scenario_route(scenario))
    reachable.update(
        f"/compare/{reference.comparison_id}"
        for reference in journey.comparisons
        if reference.comparison_id in comparisons_by_id
    )
    reachable.update(
        f"/methods/{method_id}"
        for method_id in {
            *journey.candidate_method_ids,
            *journey.conditional_method_ids,
            *journey.excluded_method_ids,
        }
        if method_id in inventories.get("method", set())
    )
    reachable.update(
        f"/sources/{source_id}"
        for source_id in journey.source_ids
        if source_id in inventories.get("source", set())
    )
    return route in reachable


def _classify_orphan_assets(
    *,
    scenario_index: VisualizationScenarioIndex,
    comparison_index: Mapping[str, Any],
    linked_scenarios: set[str],
    linked_comparisons: set[str],
    content_pages: list[ContentPage],
    linked_content: set[str],
    asset_policy: LearningJourneyAssetPolicyIndex,
) -> list[JourneyOrphanAsset]:
    assets: list[JourneyOrphanAsset] = []
    policies = {(item.asset_type, item.asset_id): item for item in asset_policy.assets}

    def orphan(
        asset_type: Literal["scenario", "comparison", "visualization_artifact", "content"],
        asset_id: str,
        default_reason: str,
    ) -> JourneyOrphanAsset:
        explicit = policies.get((asset_type, asset_id))
        return JourneyOrphanAsset(
            asset_type=asset_type,
            asset_id=asset_id,
            policy=explicit.policy if explicit else "warning",
            reason_code=explicit.reason if explicit else default_reason,
        )

    for scenario in scenario_index.scenarios:
        if scenario.scenario_id in linked_scenarios:
            continue
        assets.append(orphan("scenario", scenario.scenario_id, "scenario_without_journey"))
        for run in scenario.runs:
            assets.append(
                orphan(
                    "visualization_artifact",
                    run.artifact_id,
                    "public_artifact_without_journey",
                )
            )
    for comparison in comparison_index.get("comparisons", []):
        comparison_id = str(comparison["comparison_id"])
        if comparison_id in linked_comparisons:
            continue
        assets.append(orphan("comparison", comparison_id, "comparison_without_journey"))
    for page in content_pages:
        if page.status == "published" and page.content_id not in linked_content:
            assets.append(orphan("content", page.content_id, "published_content_without_journey"))
    unique_assets = {(item.asset_type, item.asset_id): item for item in assets}
    return sorted(unique_assets.values(), key=lambda item: (item.asset_type, item.asset_id))


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
