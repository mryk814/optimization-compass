from __future__ import annotations

import ast
import json
from pathlib import Path


def test_topology_cantilever_connects_formulation_to_visual_diagnostics() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "topology-cantilever")

    assert case["problem_archetype_id"] == "PA045"
    assert case["map_node_id"] == "answer:Q01:continuous"
    assert {"SCENARIO_TOPOLOGY_SIMP_OC", "SCENARIO_TOPOLOGY_CHECKERBOARD"} <= set(
        case["visualization_ids"]
    )
    assert case["comparison_ids"] == ["COMPARE_TOPOLOGY_OC_MMA"]
    ast.parse(case["python_example"])
    assert "generate_topology_field_artifact" in case["python_example"]
    assert "checkerboard_score" in case["python_example"]
    assert "derived state" in case["decision_variables"]
    assert "①density" in case["practical_notes"]
    assert "④gray fraction" in case["practical_notes"]
    assert "Q4 FEM解析値" in case["limitations"][0]
