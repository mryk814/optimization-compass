from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.learning_journeys import (
    LearningJourneyIndex,
    validate_learning_journey_references,
)

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "site/public/data/learning-journeys.json"


def load_index() -> LearningJourneyIndex:
    return LearningJourneyIndex.model_validate_json(FIXTURE.read_text(encoding="utf-8"))


def test_constrained_design_pilot_connects_case_to_scenario() -> None:
    index = load_index()
    pilot = next(item for item in index.journeys if item.journey_id == "constrained-design")

    assert pilot.case_id == "constrained-design"
    assert pilot.problem_archetype_id == "PA009"
    assert pilot.formulation.variable_domain_summary == "continuous"
    assert [item.scenario_id for item in pilot.scenarios] == ["SCENARIO_CONSTRAINED_DISK"]
    assert pilot.scenarios[0].canonical_url == "/theater/learning/SCENARIO_CONSTRAINED_DISK"
    assert pilot.status == "partial"
    assert pilot.completion_reasons == ["missing_comparison"]


def test_index_reports_orphan_scenarios_and_comparisons() -> None:
    index = load_index()

    assert index.orphan_scenario_ids
    assert set(index.orphan_comparison_ids).issubset(
        {"COMPARE_GRADIENT_FAMILY", "COMPARE_GRADIENT_DIVERGENCE"}
    )


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
