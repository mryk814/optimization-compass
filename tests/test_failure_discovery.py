from __future__ import annotations

import json
from pathlib import Path

from optimization_compass.failure_discovery import FailureDiscoveryIndex
from optimization_compass.site_export import export_site_data


def test_failure_discovery_joins_structured_failures_and_case_exclusions(
    tmp_path: Path, repository
) -> None:
    export_site_data(tmp_path, repository)
    index = FailureDiscoveryIndex.model_validate_json(
        (tmp_path / "failure-discovery.json").read_bytes()
    )

    assert index.summary.total_entries == 30
    assert index.summary.structured_failure_count == 12
    assert index.summary.case_exclusion_count == 18
    assert {entry.entry_kind for entry in index.entries} == {
        "structured_failure",
        "case_exclusion",
    }
    exclusions = [entry for entry in index.entries if entry.entry_kind == "case_exclusion"]
    assert all(entry.disposition == "excluded" for entry in exclusions)
    assert all(entry.case_context is not None for entry in exclusions)
    assert all(entry.method_ids for entry in exclusions)


def test_failure_discovery_is_deterministic(tmp_path: Path, repository) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    export_site_data(first, repository)
    export_site_data(second, repository)
    assert (first / "failure-discovery.json").read_bytes() == (
        second / "failure-discovery.json"
    ).read_bytes()
    assert json.loads((first / "failure-discovery.json").read_bytes())["entries"]
