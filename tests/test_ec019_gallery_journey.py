from __future__ import annotations

import ast
import json
from pathlib import Path


def test_ec019_has_a_complete_time_window_routing_teaching_instance() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "EC019")

    assert case["problem_archetype_id"] == "PA031"
    assert len(case["question_answers"]) == 12
    assert case["question_answers"]["Q11"] == "scheduling_routing"
    assert case["map_node_id"] == "answer:Q11:scheduling_routing"
    assert {item["method_id"] for item in case["candidate_methods"]} == {
        "M_LOCAL_SEARCH_COMBINATORIAL"
    }
    assert {"S022", "S023", "S024", "S053", "S054", "S079"} <= set(
        case["source_ids"]
    )
    ast.parse(case["python_example"])
    assert "RoutingIndexManager(5, 1, 0)" in case["python_example"]
    assert "time_windows" in case["python_example"]
    assert "hard constraint" in case["objective"]
    assert "最適性は未証明" in case["practical_notes"]
    assert "1000 stop" in case["limitations"][0]
    assert "大域最適性を保証せず" in case["limitations"][1]
