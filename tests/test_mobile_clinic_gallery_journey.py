from __future__ import annotations

import ast
import json
from pathlib import Path

from optimization_compass.comparisons import load_comparison_seed


def test_mobile_clinic_case_is_a_bounded_healthcare_teaching_case() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(
        item
        for item in gallery["cases"]
        if item["case_id"] == "mobile-clinic-outreach-selection"
    )

    assert case["domain"] == "healthcare"
    assert case["problem_archetype_id"] == "PA032"
    assert case["question_answers"]["Q01"] == "binary"
    assert case["map_node_id"] == "answer:Q01:binary"
    assert case["comparison_ids"] == ["COMPARE_MOBILE_CLINIC_BNB_BUDGET"]
    assert {item["method_id"] for item in case["candidate_methods"]}.isdisjoint(
        item["method_id"] for item in case["conditional_methods"]
    )
    assert {item["method_id"] for item in case["candidate_methods"]}.isdisjoint(
        item["method_id"] for item in case["excluded_methods"]
    )
    ast.parse(case["python_example"])
    assert "保証する値ではない" in case["objective"]
    assert "4品目knapsack" in case["practical_notes"]
    assert "医療上の有効性" in case["limitations"][1]


def test_mobile_clinic_comparison_changes_only_the_node_stop_limit() -> None:
    index = load_comparison_seed(Path("data/seeds/site_comparisons.json"), "test")
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_MOBILE_CLINIC_BNB_BUDGET"
    )

    assert comparison.journey_id == comparison.case_id == "mobile-clinic-outreach-selection"
    assert comparison.mode == "failure_contrast"
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False
    assert comparison.budget.metric == comparison.synchronization_axis
    assert comparison.changed_factors == ["node_stop_limitだけを9から4へ変える"]
    assert {member.parameters["node_stop_limit"] for member in comparison.members} == {4, 9}
    assert len({member.scenario_id for member in comparison.members}) == 2
