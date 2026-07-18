from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

from optimization_compass.coverage import CoverageReport, build_coverage_report, diff_coverage
from optimization_compass.db import KnowledgeRepository

ROOT = Path(__file__).parents[1]


def load_report() -> CoverageReport:
    return CoverageReport.model_validate_json(
        (ROOT / "site/public/data/coverage.json").read_text(encoding="utf-8")
    )


def test_report_separates_inventory_from_expected_coverage() -> None:
    report = load_report()
    assert report.summary.subject_counts == {
        "feature_family": 10,
        "method": 105,
        "problem": 56,
    }
    assert len(report.subjects) == 171
    assert len(report.expectations) == 11
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
    assert report.integrity_issues == []
    discrete = next(
        item for item in report.expectations if item.expectation_id == "COV_DISCRETE_SEARCH_TREE"
    )
    assert discrete.status == "available"
    assert discrete.reason_codes == []
    assert discrete.artifact_ids == ["binary-knapsack-bnb-complete"]
    assert discrete.route_ids == ["/theater/search-tree/binary-knapsack-bnb-complete"]


def test_priority_order_is_deterministic_and_ignores_popularity() -> None:
    report = load_report()
    assert [item.rank for item in report.priorities] == list(range(1, 7))
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
    missing = next(
        expectation
        for expectation in after_payload["expectations"]
        if expectation["status"] == "missing"
    )
    missing["status"] = "available"
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
        "SCENARIO_BO_1D_MULTIFIDELITY_LEDGER",
    ]
    assert expectation.route_ids == [
        "/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_NOISELESS",
        "/theater/bayesian-optimization/SCENARIO_BO_1D_MULTIFIDELITY_LEDGER",
    ]


def test_learning_slices_close_constrained_and_multiobjective_coverage() -> None:
    report = load_report()
    expected = {
        "COV_CONSTRAINED_FEASIBLE": (
            ["SCENARIO_CONSTRAINED_DISK", "SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH"],
            ["/theater/learning/SCENARIO_CONSTRAINED_DISK"],
        ),
        "COV_MULTI_OBJECTIVE_PARETO": (
            [
                "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY",
                "SCENARIO_BIOBJECTIVE_QUADRATIC",
            ],
            ["/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC"],
        ),
    }

    for expectation_id, (scenario_ids, route_ids) in expected.items():
        expectation = next(
            item for item in report.expectations if item.expectation_id == expectation_id
        )
        assert expectation.status == "available"
        assert expectation.scenario_ids == scenario_ids
        assert expectation.route_ids == route_ids


def test_generated_slices_declare_their_canonical_identity() -> None:
    report = load_report()
    scenario_index = json.loads(
        (ROOT / "site/public/data/visualization-scenarios.json").read_text(encoding="utf-8")
    )
    derived = [item for item in scenario_index["scenarios"] if item["identity_status"] == "derived"]
    generated_only = [
        item for item in scenario_index["scenarios"] if item["identity_status"] == "generated_only"
    ]
    assert derived
    assert generated_only
    assert all(item["canonical_scenario_id"] for item in derived)
    assert all(item["canonical_scenario_id"] is None for item in generated_only)
    assert report.integrity_issues == []


def test_coverage_rejects_broken_canonical_identity_relations(tmp_path: Path) -> None:
    artifact_root = tmp_path / "site-data"
    shutil.copytree(ROOT / "site/public/data", artifact_root)
    scenarios_path = artifact_root / "visualization-scenarios.json"
    scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
    derived_scenario = next(
        item for item in scenarios["scenarios"] if item["identity_status"] == "derived"
    )
    derived_scenario["canonical_scenario_id"] = "SCENARIO_MISSING"
    scenarios_path.write_text(json.dumps(scenarios), encoding="utf-8")

    comparisons_path = artifact_root / "comparisons.json"
    comparisons = json.loads(comparisons_path.read_text(encoding="utf-8"))
    derived_comparison = next(
        item for item in comparisons["comparisons"] if item["identity_status"] == "derived"
    )
    derived_comparison["canonical_comparison_id"] = "COMPARE_MISSING"
    comparisons_path.write_text(json.dumps(comparisons), encoding="utf-8")

    baseline = load_report()
    report = build_coverage_report(
        KnowledgeRepository(),
        artifact_root,
        dataset_version=baseline.dataset_version,
        generated_at=baseline.generated_at,
    )

    assert {(issue.code, issue.entity_id) for issue in report.integrity_issues} >= {
        ("broken_scenario_alias", "SCENARIO_MISSING"),
        ("broken_comparison_alias", "COMPARE_MISSING"),
    }


def test_gallery_candidate_objects_restore_method_coverage_without_reverse_links(
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "site-data"
    shutil.copytree(ROOT / "site/public/data", artifact_root)
    links_path = artifact_root / "entity-links.json"
    links = json.loads(links_path.read_text(encoding="utf-8"))
    cp_sat = next(
        item
        for item in links["entities"]
        if item["entity_type"] == "method" and item["entity_id"] == "M_CP_SAT"
    )
    cp_sat["relations"] = [
        relation for relation in cp_sat["relations"] if relation["target_type"] != "case"
    ]
    links_path.write_text(json.dumps(links), encoding="utf-8")

    baseline = load_report()
    report = build_coverage_report(
        KnowledgeRepository(),
        artifact_root,
        dataset_version=baseline.dataset_version,
        generated_at=baseline.generated_at,
    )
    subject = next(item for item in report.subjects if item.subject_id == "M_CP_SAT")

    assert set(subject.dimensions["gallery"].target_ids) >= {
        "budget-allocation",
        "shift-scheduling",
    }


def test_coverage_reports_orphaned_failure_discovery_references(tmp_path: Path) -> None:
    artifact_root = tmp_path / "site-data"
    shutil.copytree(ROOT / "site/public/data", artifact_root)
    failure_path = artifact_root / "failure-discovery.json"
    payload = json.loads(failure_path.read_text(encoding="utf-8"))
    exclusion = next(
        entry for entry in payload["entries"] if entry["entry_kind"] == "case_exclusion"
    )
    exclusion["case_id"] = "CASE_MISSING"
    failure_path.write_text(json.dumps(payload), encoding="utf-8")

    baseline = load_report()
    report = build_coverage_report(
        KnowledgeRepository(),
        artifact_root,
        dataset_version=baseline.dataset_version,
        generated_at=baseline.generated_at,
    )

    assert any(
        issue.code == "failure_discovery_missing_case" and issue.entity_id == exclusion["entry_id"]
        for issue in report.integrity_issues
    )
