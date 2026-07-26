from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.content_models import load_content
from optimization_compass.evidence import SourceEvidenceIndex
from optimization_compass.learning_journey_policy import LearningJourneyAssetPolicyIndex
from optimization_compass.learning_journeys import (
    JourneyComparisonReference,
    LearningJourneyIndex,
    _classify_orphan_assets,
    _comparison_issues,
    _primary_scenario,
    _reject_broken_routes_for_otherwise_complete_journey,
    _reject_error_orphans,
    _route_is_reachable,
    _scenario_role,
    _source_review_issues,
    validate_learning_journey_references,
)
from optimization_compass.visualization_scenarios import VisualizationScenarioIndex

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "site/public/data/learning-journeys.json"
SCENARIO_FIXTURE = ROOT / "site/public/data/visualization-scenarios.json"
COMPARISON_FIXTURE = ROOT / "site/public/data/comparisons.json"
GALLERY_FIXTURE = ROOT / "site/public/data/gallery.json"
SOURCE_FIXTURE = ROOT / "site/public/data/sources.json"


def load_index() -> LearningJourneyIndex:
    return LearningJourneyIndex.model_validate_json(FIXTURE.read_text(encoding="utf-8"))


def test_constrained_design_pilot_connects_case_to_scenario() -> None:
    index = load_index()
    pilot = next(item for item in index.journeys if item.journey_id == "constrained-design")

    assert pilot.case_id == "constrained-design"
    assert pilot.problem_archetype_id == "PA009"
    assert pilot.formulation.variable_domain_summary.startswith("固定教材では ")
    assert "<math" in pilot.formulation.variable_domain_summary
    scenario_roles = {item.role: item for item in pilot.scenarios}
    assert set(scenario_roles) == {"primary", "failure_contrast"}
    assert scenario_roles["primary"].scenario_id == "SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH"
    assert scenario_roles["primary"].canonical_url == (
        "/theater/learning/SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH"
    )
    assert scenario_roles["failure_contrast"].scenario_id == "SCENARIO_CONSTRAINED_DISK"
    assert pilot.status == "complete"
    assert pilot.completion_reasons == []
    assessment = next(item for item in index.assessments if item.journey_id == "constrained-design")
    assert assessment.missing_dimensions == []
    assert assessment.dimensions["alternate_scenario"].state == "complete"
    assert assessment.dimensions["canonical_comparison"].state == "complete"
    assert sum(index.summary.status_counts.values()) == len(index.journeys)
    assert index.summary.status_counts["draft"] == 0


def test_parameter_estimation_journey_connects_primary_sensitivity_and_comparison() -> None:
    index = load_index()
    journey = next(item for item in index.journeys if item.journey_id == "EC013")

    assert journey.status == "complete"
    assert journey.completion_reasons == []
    assert {item.role for item in journey.scenarios} == {"primary", "alternate", "sensitivity"}
    assert next(item for item in journey.scenarios if item.role == "primary").scenario_id == (
        "SCENARIO_EXPONENTIAL_FIT_TRF"
    )
    assert {item.comparison_id for item in journey.comparisons} == {
        "COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS"
    }


def test_expensive_black_box_journey_reuses_bo_scenarios_and_related_comparisons() -> None:
    index = load_index()
    journey = next(item for item in index.journeys if item.journey_id == "hyperparameter-search")

    assert journey.problem_archetype_id == "PA039"
    assert journey.problem_instance_ids == ["OBJECTIVE_EDUCATIONAL_WAVY_1D"]
    assert journey.status == "complete"
    assert journey.completion_reasons == []
    primary = next(item for item in journey.scenarios if item.role == "primary")
    assert primary.scenario_id == "SCENARIO_BO_1D_EXPLORE_NOISELESS"
    assert primary.canonical_url == (
        "/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_NOISELESS"
    )
    assert {item.role for item in journey.scenarios} == {"primary", "sensitivity"}
    assert {item.comparison_id for item in journey.comparisons} == {
        "COMPARE_BO_ACQUISITION_NOISE_BASELINE",
        "COMPARE_NELDER_MEAD_INITIAL_SIMPLEX",
    }
    assessment = next(
        item for item in index.assessments if item.journey_id == "hyperparameter-search"
    )
    assert assessment.missing_dimensions == []


def test_multiobjective_journey_separates_front_generation_from_preference_selection() -> None:
    index = load_index()
    journey = next(item for item in index.journeys if item.journey_id == "EC017")

    assert journey.status == "complete"
    assert journey.completion_reasons == []
    assert {(item.role, item.scenario_id) for item in journey.scenarios} == {
        ("primary", "SCENARIO_BIOBJECTIVE_QUADRATIC"),
        ("sensitivity", "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY"),
    }
    assert {item.comparison_id for item in journey.comparisons} == {"COMPARE_PARETO_PREFERENCE"}
    assessment = next(item for item in index.assessments if item.journey_id == "EC017")
    assert assessment.missing_dimensions == []
    assert assessment.dimensions["alternate_scenario"].target_ids == [
        "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY"
    ]


def test_index_reports_summary_and_explicit_orphan_policies() -> None:
    index = load_index()

    assert index.summary.target_complete_journeys == 5
    assert index.summary.total_journeys == len(index.journeys)
    assert sum(index.summary.status_counts.values()) == len(index.journeys)
    assert {item.policy for item in index.orphan_assets} == {"warning"}
    assert any(
        item.asset_type == "scenario" and item.policy == "warning" for item in index.orphan_assets
    )
    orphan_ids = {item.asset_id for item in index.orphan_assets}
    assert "COMPARE_GRADIENT_FAMILY" not in orphan_ids
    assert "COMPARE_GRADIENT_DIVERGENCE" not in orphan_ids
    assert any(item.asset_type == "visualization_artifact" for item in index.orphan_assets)
    assert any(item.asset_type == "content" for item in index.orphan_assets)


def test_explicit_policy_marks_an_orphan_as_intentionally_standalone() -> None:
    index = load_index()
    scenarios = VisualizationScenarioIndex.model_validate_json(
        SCENARIO_FIXTURE.read_text(encoding="utf-8")
    )
    comparisons = json.loads(COMPARISON_FIXTURE.read_text(encoding="utf-8"))
    linked_scenarios = {
        reference.scenario_id for journey in index.journeys for reference in journey.scenarios
    }
    standalone_id = next(
        scenario.scenario_id
        for scenario in scenarios.scenarios
        if scenario.scenario_id not in linked_scenarios
    )
    policy = LearningJourneyAssetPolicyIndex.model_validate(
        {
            "contract_version": "1.0.0",
            "assets": [
                {
                    "asset_type": "scenario",
                    "asset_id": standalone_id,
                    "policy": "standalone",
                    "reason": "intentionally_standalone_demo",
                }
            ],
        }
    )
    classified = _classify_orphan_assets(
        scenario_index=scenarios,
        comparison_index=comparisons,
        linked_scenarios=linked_scenarios,
        linked_comparisons={
            reference.comparison_id
            for journey in index.journeys
            for reference in journey.comparisons
        },
        content_pages=load_content(ROOT / "content"),
        linked_content={item for journey in index.journeys for item in journey.content_ids},
        asset_policy=policy,
    )

    standalone = next(
        item
        for item in classified
        if item.asset_type == "scenario" and item.asset_id == standalone_id
    )
    assert standalone.policy == "standalone"
    assert standalone.reason_code == "intentionally_standalone_demo"

    with pytest.raises(ValueError, match=f"scenario:{standalone_id}"):
        _reject_error_orphans([standalone.model_copy(update={"policy": "error"})])


def test_index_rejects_duplicate_and_cross_version_journeys() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["journeys"][1]["journey_id"] = payload["journeys"][0]["journey_id"]
    payload["journeys"][1]["case_id"] = payload["journeys"][0]["case_id"]
    payload["journeys"][1]["canonical_url"] = payload["journeys"][0]["canonical_url"]
    with pytest.raises(ValidationError, match="journey IDs must be unique"):
        LearningJourneyIndex.model_validate(payload)

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["journeys"][0]["dataset_version"] = "other"
    with pytest.raises(ValidationError, match="dataset version"):
        LearningJourneyIndex.model_validate(payload)


def test_index_rejects_missing_and_circular_relations() -> None:
    index = load_index()
    scenario_ids = {
        reference.scenario_id for journey in index.journeys for reference in journey.scenarios
    }
    inventories = {
        "case": {journey.case_id for journey in index.journeys},
        "problem": {journey.problem_archetype_id for journey in index.journeys},
        "scenario": scenario_ids - {next(iter(scenario_ids))},
        "comparison": {
            reference.comparison_id
            for journey in index.journeys
            for reference in journey.comparisons
        },
        "method": {
            method_id
            for journey in index.journeys
            for method_id in [
                *journey.candidate_method_ids,
                *journey.conditional_method_ids,
                *journey.excluded_method_ids,
            ]
        },
        "implementation": {
            item for journey in index.journeys for item in journey.implementation_ids
        },
        "content": {item for journey in index.journeys for item in journey.content_ids},
        "source": {item for journey in index.journeys for item in journey.source_ids},
    }
    with pytest.raises(ValueError, match="missing scenario references"):
        validate_learning_journey_references(index, inventories=inventories)

    payload = index.model_dump(mode="json")
    first_id = payload["journeys"][0]["journey_id"]
    second_id = payload["journeys"][1]["journey_id"]
    payload["journeys"][0]["prerequisite_journey_ids"] = [second_id]
    payload["journeys"][1]["prerequisite_journey_ids"] = [first_id]
    with pytest.raises(ValidationError, match="circular journey prerequisite"):
        LearningJourneyIndex.model_validate(payload)


def test_index_rejects_complete_journey_with_missing_dimension() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assessment = payload["assessments"][0]
    assessment["dimensions"]["primary_scenario"]["state"] = "missing"
    assessment["dimensions"]["primary_scenario"]["reason_codes"] = ["missing_primary_scenario"]
    assessment["missing_dimensions"] = ["primary_scenario"]

    with pytest.raises(ValidationError, match="cannot have missing dimensions"):
        LearningJourneyIndex.model_validate(payload)


def test_completeness_checks_comparison_contract_and_real_route_targets() -> None:
    index = load_index()
    journey = next(item for item in index.journeys if item.journey_id == "constrained-design")
    comparison_payload = json.loads(COMPARISON_FIXTURE.read_text(encoding="utf-8"))
    comparisons = {item["comparison_id"]: item for item in comparison_payload["comparisons"]}
    assert _comparison_issues(journey, comparisons_by_id=comparisons) == []

    canonical = comparisons["COMPARE_CONSTRAINED_FAILURE"]
    derived = json.loads(json.dumps(canonical))
    derived["comparison_id"] = "COMPARE_CONSTRAINED_FAILURE_SENSITIVITY"
    derived["canonical_url"] = "/compare/COMPARE_CONSTRAINED_FAILURE_SENSITIVITY"
    derived["identity_status"] = "derived"
    derived["canonical_comparison_id"] = "COMPARE_CONSTRAINED_FAILURE"
    mixed_journey = journey.model_copy(
        update={
            "comparisons": [
                *journey.comparisons,
                JourneyComparisonReference(
                    comparison_id=derived["comparison_id"],
                    canonical_url=derived["canonical_url"],
                ),
            ]
        }
    )
    assert (
        _comparison_issues(
            mixed_journey,
            comparisons_by_id={
                "COMPARE_CONSTRAINED_FAILURE": canonical,
                derived["comparison_id"]: derived,
            },
        )
        == []
    )

    derived_only_journey = journey.model_copy(update={"comparisons": mixed_journey.comparisons[1:]})
    assert _comparison_issues(
        derived_only_journey,
        comparisons_by_id={derived["comparison_id"]: derived},
    ) == [
        "comparison_not_canonical",
        "derived_comparison_without_canonical",
    ]

    broken = json.loads(json.dumps(comparisons["COMPARE_CONSTRAINED_FAILURE"]))
    broken["fixed_factors"] = []
    broken["case_id"] = "other-case"
    broken["problem_instance_id"] = "OTHER_INSTANCE"
    issues = _comparison_issues(
        journey,
        comparisons_by_id={"COMPARE_CONSTRAINED_FAILURE": broken},
    )
    assert issues == ["comparison_contract_incomplete", "comparison_wrong_journey"]

    shared_instance = json.loads(json.dumps(comparisons["COMPARE_CONSTRAINED_FAILURE"]))
    shared_instance["case_id"] = "source-case"
    shared_instance["journey_id"] = "source-journey"
    assert (
        _comparison_issues(
            journey,
            comparisons_by_id={"COMPARE_CONSTRAINED_FAILURE": shared_instance},
        )
        == []
    )

    scenarios = VisualizationScenarioIndex.model_validate_json(
        SCENARIO_FIXTURE.read_text(encoding="utf-8")
    )
    scenario_by_id = {item.scenario_id: item for item in scenarios.scenarios}
    inventories = {
        "method": {
            *journey.candidate_method_ids,
            *journey.conditional_method_ids,
            *journey.excluded_method_ids,
        },
        "source": set(journey.source_ids),
    }
    assert _route_is_reachable(
        journey.scenarios[0].canonical_url,
        journey=journey,
        scenarios_by_id=scenario_by_id,
        comparisons_by_id=comparisons,
        inventories=inventories,
    )
    assert not _route_is_reachable(
        "/methods/M_MISSING",
        journey=journey,
        scenarios_by_id=scenario_by_id,
        comparisons_by_id=comparisons,
        inventories=inventories,
    )


def test_public_otherwise_complete_journey_rejects_a_broken_route() -> None:
    with pytest.raises(ValueError, match="public complete journey pilot has broken routes"):
        _reject_broken_routes_for_otherwise_complete_journey(
            journey_id="pilot",
            broken_routes=["/compare/missing"],
            non_route_missing=[],
            reference_issues={},
        )

    _reject_broken_routes_for_otherwise_complete_journey(
        journey_id="partial",
        broken_routes=["/compare/missing"],
        non_route_missing=["canonical_comparison"],
        reference_issues={},
    )


def test_source_review_uses_surface_sources_and_type_specific_freshness() -> None:
    index = load_index()
    journey = next(item for item in index.journeys if item.journey_id == "constrained-design")
    scenarios = VisualizationScenarioIndex.model_validate_json(
        SCENARIO_FIXTURE.read_text(encoding="utf-8")
    )
    comparisons_payload = json.loads(COMPARISON_FIXTURE.read_text(encoding="utf-8"))
    gallery_payload = json.loads(GALLERY_FIXTURE.read_text(encoding="utf-8"))
    source_index = SourceEvidenceIndex.model_validate_json(
        SOURCE_FIXTURE.read_text(encoding="utf-8")
    )
    case = next(item for item in gallery_payload["cases"] if item["case_id"] == journey.case_id)
    kwargs = {
        "case": case,
        "scenarios_by_id": {item.scenario_id: item for item in scenarios.scenarios},
        "comparisons_by_id": {
            item["comparison_id"]: item for item in comparisons_payload["comparisons"]
        },
        "content_pages": load_content(ROOT / "content"),
        "generated_at": index.generated_at,
    }

    assert _source_review_issues(journey, source_index=source_index, **kwargs) == []

    stale_source_id = journey.source_ids[0]
    stale_index = source_index.model_copy(
        update={
            "sources": [
                source.model_copy(update={"last_verified": date(2000, 1, 1)})
                if source.source_id == stale_source_id
                else source
                for source in source_index.sources
            ]
        }
    )
    assert "stale_source" in _source_review_issues(
        journey,
        source_index=stale_index,
        **kwargs,
    )


def test_source_review_accepts_case_review_after_dataset_release() -> None:
    index = load_index()
    journey = next(item for item in index.journeys if item.journey_id == "constrained-design")
    scenarios = VisualizationScenarioIndex.model_validate_json(
        SCENARIO_FIXTURE.read_text(encoding="utf-8")
    )
    comparisons_payload = json.loads(COMPARISON_FIXTURE.read_text(encoding="utf-8"))
    gallery_payload = json.loads(GALLERY_FIXTURE.read_text(encoding="utf-8"))
    source_index = SourceEvidenceIndex.model_validate_json(
        SOURCE_FIXTURE.read_text(encoding="utf-8")
    )
    case = next(item for item in gallery_payload["cases"] if item["case_id"] == journey.case_id)

    issues = _source_review_issues(
        journey.model_copy(update={"last_reviewed": "2026-07-24"}),
        case={**case, "last_reviewed": "2026-07-24"},
        scenarios_by_id={item.scenario_id: item for item in scenarios.scenarios},
        comparisons_by_id={
            item["comparison_id"]: item for item in comparisons_payload["comparisons"]
        },
        content_pages=load_content(ROOT / "content"),
        source_index=source_index,
        generated_at=datetime(2026, 7, 19, tzinfo=UTC),
    )

    assert "stale_case_review" not in issues


def test_source_review_accepts_current_version_original_paper() -> None:
    index = load_index()
    journey = next(item for item in index.journeys if item.journey_id == "shape-diffuser")
    scenarios = VisualizationScenarioIndex.model_validate_json(
        SCENARIO_FIXTURE.read_text(encoding="utf-8")
    )
    comparisons_payload = json.loads(COMPARISON_FIXTURE.read_text(encoding="utf-8"))
    gallery_payload = json.loads(GALLERY_FIXTURE.read_text(encoding="utf-8"))
    source_index = SourceEvidenceIndex.model_validate_json(
        SOURCE_FIXTURE.read_text(encoding="utf-8")
    )
    case = next(item for item in gallery_payload["cases"] if item["case_id"] == journey.case_id)

    issues = _source_review_issues(
        journey,
        case=case,
        scenarios_by_id={item.scenario_id: item for item in scenarios.scenarios},
        comparisons_by_id={
            item["comparison_id"]: item for item in comparisons_payload["comparisons"]
        },
        content_pages=load_content(ROOT / "content"),
        source_index=source_index,
        generated_at=index.generated_at,
    )

    assert "invalid_source_currentness" not in issues


def test_primary_scenario_keeps_failure_contrast_in_a_diagnostic_role() -> None:
    scenarios = VisualizationScenarioIndex.model_validate_json(
        SCENARIO_FIXTURE.read_text(encoding="utf-8")
    )
    selected = [
        item
        for item in scenarios.scenarios
        if item.scenario_id
        in {
            "SCENARIO_ADAM_QUADRATIC",
            "SCENARIO_ADAM_QUADRATIC_DIVERGENCE",
        }
    ]

    primary = _primary_scenario(selected)

    assert primary is not None
    assert primary.scenario_id == "SCENARIO_ADAM_QUADRATIC"
    divergence = next(
        item for item in selected if item.scenario_id == "SCENARIO_ADAM_QUADRATIC_DIVERGENCE"
    )
    assert _scenario_role(divergence, primary) == "failure_contrast"
