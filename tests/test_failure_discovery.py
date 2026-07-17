from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from optimization_compass.db import KnowledgeRepository
from optimization_compass.failure_discovery import (
    FailureDiscoveryIndex,
    build_failure_discovery_index,
)
from optimization_compass.learning_journeys import LearningJourneyIndex

ROOT = Path(__file__).parents[1]


def load_index() -> FailureDiscoveryIndex:
    """Rebuild the discovery index from the same public authorities used by the exporter."""
    gallery = json.loads((ROOT / "site/public/data/gallery.json").read_text(encoding="utf-8"))
    journeys = LearningJourneyIndex.model_validate_json(
        (ROOT / "site/public/data/learning-journeys.json").read_text(encoding="utf-8")
    )
    return build_failure_discovery_index(
        KnowledgeRepository(),
        dataset_version=gallery["dataset_version"],
        generated_at=datetime.fromisoformat(journeys.generated_at.isoformat()),
        gallery_index=gallery,
        learning_journeys=journeys,
    )


def test_failure_discovery_unifies_profiles_and_case_exclusions_without_flattening_semantics() -> (
    None
):
    index = load_index()

    assert index.summary.structured_failure_count == 12
    assert index.summary.case_exclusion_count == 11
    assert index.summary.total_entries == 23
    assert [item.entry_id for item in index.entries] == sorted(
        item.entry_id for item in index.entries
    )

    structured = next(item for item in index.entries if item.entry_id == "structured:FM003")
    assert structured.entry_kind == "structured_failure"
    assert structured.disposition == "excluded"
    assert structured.severity == "high"
    assert structured.diagnostics and structured.mitigations
    assert "M_BFGS" in structured.method_ids

    case_exclusion = next(
        item for item in index.entries if item.entry_id == "case:constrained-design:M_BFGS"
    )
    assert case_exclusion.entry_kind == "case_exclusion"
    assert case_exclusion.scope == "case_specific"
    assert case_exclusion.severity == "not_applicable"
    assert case_exclusion.case_context is not None
    assert case_exclusion.method_ids == ["M_BFGS"]
    assert set(case_exclusion.related_failure_mode_ids) >= {"FM003", "FM007", "FM016"}
    assert set(case_exclusion.scenario_ids) == {
        "SCENARIO_CONSTRAINED_DISK",
        "SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH",
    }


def test_at_least_three_case_exclusions_form_source_backed_scenario_journeys() -> None:
    index = load_index()
    complete = [
        item
        for item in index.entries
        if item.entry_kind == "case_exclusion"
        and item.case_id
        and item.method_ids
        and item.source_ids
        and item.scenario_ids
    ]

    assert len(complete) >= 3
