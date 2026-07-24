from __future__ import annotations

import ast
import json
from pathlib import Path


def test_budget_allocation_connects_solution_to_search_tree_proof() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "budget-allocation")

    assert case["problem_archetype_id"] == "PA032"
    assert case["map_node_id"] == "answer:Q01:binary"
    assert {"SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE", "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET"} <= set(
        case["visualization_ids"]
    )
    assert case["comparison_ids"] == ["COMPARE_KNAPSACK_BNB_BUDGET"]
    ast.parse(case["python_example"])
    assert '"selected": selected' in case["python_example"]
    assert "best_objective_bound" in case["python_example"]
    assert "①nodeの部分assignment" in case["practical_notes"]
    assert "value 15" in case["practical_notes"]
    assert "一般性能を順位付けしない" in case["limitations"][1]
