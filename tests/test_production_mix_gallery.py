from __future__ import annotations

import ast
import json
from pathlib import Path


def test_production_mix_case_exposes_a_bounded_milp_journey() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "production-mix-planning")

    assert case["problem_archetype_id"] == "PA023"
    assert case["map_node_id"] == "answer:Q01:mixed"
    assert case["candidate_methods"] == [
        {
            "method_id": "M_BRANCH_CUT",
            "reason": (
                "連続の生産量と0-1の段取り判断を同じ線形modelで保ち、実行可能な計画、"
                "relaxation bound、optimality gapを分けて確認できるため"
            ),
        }
    ]
    assert case["implementation_ids"] == ["I_SCIPY_MILP_HIGHS"]
    assert {
        "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE",
        "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET",
    } <= set(case["visualization_ids"])
    assert case["comparison_ids"] == ["COMPARE_KNAPSACK_BNB_BUDGET"]

    ast.parse(case["python_example"])
    assert "integrality = np.array([0, 0, 1, 1])" in case["python_example"]
    assert "LinearConstraint" in case["python_example"]
    assert "この生産計画のsolver実行や利益比較ではない" in case["practical_notes"]
    assert "一般性能を順位付けしない" in case["limitations"][-1]
