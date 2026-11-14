from __future__ import annotations

import json
from typing import TYPE_CHECKING

from optimization_compass.failure_discovery import FailureDiscoveryIndex

if TYPE_CHECKING:
    from conftest import SiteExportPair


def test_failure_discovery_joins_structured_failures_and_case_exclusions(
    site_export_pair: SiteExportPair,
) -> None:
    index = FailureDiscoveryIndex.model_validate_json(
        (site_export_pair.first / "failure-discovery.json").read_bytes()
    )

    assert {entry.entry_kind for entry in index.entries} == {
        "structured_failure",
        "case_exclusion",
    }
    exclusions = [entry for entry in index.entries if entry.entry_kind == "case_exclusion"]
    structured = [entry for entry in index.entries if entry.entry_kind == "structured_failure"]
    assert index.summary.total_entries == len(index.entries)
    assert index.summary.structured_failure_count == len(structured)
    assert index.summary.case_exclusion_count == len(exclusions)
    assert index.summary.entries_with_scenarios == sum(
        bool(entry.scenario_ids) for entry in index.entries
    )
    assert any(entry.case_id == "traffic-signal-tradeoff" for entry in exclusions)
    assert all(entry.disposition == "excluded" for entry in exclusions)
    assert all(entry.case_context is not None for entry in exclusions)
    assert all(entry.method_ids for entry in exclusions)


def test_failure_discovery_is_deterministic(site_export_pair: SiteExportPair) -> None:
    first = site_export_pair.first
    second = site_export_pair.second
    assert (first / "failure-discovery.json").read_bytes() == (
        second / "failure-discovery.json"
    ).read_bytes()
    assert json.loads((first / "failure-discovery.json").read_bytes())["entries"]
