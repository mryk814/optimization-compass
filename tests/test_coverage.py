from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from optimization_compass.coverage import CoverageReport, diff_coverage

ROOT = Path(__file__).parents[1]


def load_report() -> CoverageReport:
    return CoverageReport.model_validate_json(
        (ROOT / "site/public/data/coverage.json").read_text(encoding="utf-8")
    )


def test_report_separates_inventory_from_expected_coverage() -> None:
    report = load_report()
    assert report.summary.subject_counts == {
        "feature_family": 10,
        "method": 98,
        "problem": 56,
    }
    assert len(report.subjects) == 164
    assert len(report.expectations) == 8
    assert set(report.summary.status_counts) == {
        "available",
        "partial",
        "missing",
        "not_applicable",
    }
    assert not hasattr(report.summary, "coverage_percent")


def test_current_artifacts_are_partial_without_inferred_renderer_contract() -> None:
    report = load_report()
    nelder_mead = next(
        item for item in report.expectations if item.expectation_id == "COV_NM_MECHANISM"
    )
    assert nelder_mead.status == "partial"
    assert nelder_mead.reason_codes == ["scenario_contract_incomplete"]
    assert nelder_mead.artifact_ids == []


def test_broken_references_are_distinct_from_unbuilt_scenarios() -> None:
    report = load_report()
    codes = {(item.code, item.entity_id) for item in report.integrity_issues}
    assert ("broken_scenario_id", "SCENARIO_GD_QUADRATIC") in codes
    assert ("orphan_comparison", "COMPARE_FIRST_ORDER_ROSENBROCK") in codes
    discrete = next(
        item for item in report.expectations if item.expectation_id == "COV_DISCRETE_SEARCH_TREE"
    )
    assert discrete.status == "available"
    assert discrete.reason_codes == []
    assert discrete.artifact_ids == ["binary-knapsack-bnb-complete"]
    assert discrete.route_ids == ["/theater/search-tree/binary-knapsack-bnb-complete"]


def test_priority_order_is_deterministic_and_ignores_popularity() -> None:
    report = load_report()
    assert [item.rank for item in report.priorities] == list(range(1, 6))
    assert [(item.total, item.slice_id) for item in report.priorities] == sorted(
        ((item.total, item.slice_id) for item in report.priorities),
        key=lambda item: (-item[0], item[1]),
    )
    assert all(
        set(item.factors) == {"classification", "misconception", "visualization", "demand"}
        for item in report.priorities
    )


def test_explicit_release_delta_reports_transitions() -> None:
    before_payload = json.loads(load_report().model_dump_json())
    after_payload = deepcopy(before_payload)
    after_payload["dataset_version"] = "0.4.0"
    after_payload["expectations"][0]["status"] = "available"
    after_payload["summary"]["status_counts"]["missing"] -= 1
    after_payload["summary"]["status_counts"]["available"] += 1
    delta = diff_coverage(
        CoverageReport.model_validate_json(json.dumps(before_payload)),
        CoverageReport.model_validate_json(json.dumps(after_payload)),
    )
    assert delta.available_delta == 1
    assert sum(delta.transitions.values()) == 1


def test_canonical_visualization_scenarios_cover_expensive_and_discrete_slices() -> None:
    report = load_report()
    expectation = next(
        item for item in report.expectations if item.expectation_id == "COV_EXPENSIVE_SURROGATE"
    )
    assert expectation.status == "available"
    assert expectation.scenario_ids == [
        "SCENARIO_BO_1D_EXPLOIT_NOISELESS",
        "SCENARIO_BO_1D_EXPLOIT_SMALL_NOISE",
        "SCENARIO_BO_1D_EXPLORE_NOISELESS",
        "SCENARIO_BO_1D_EXPLORE_SMALL_NOISE",
    ]
    assert expectation.route_ids == [
        "/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_NOISELESS"
    ]
