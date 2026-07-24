from __future__ import annotations

import ast
import json
from pathlib import Path


def test_portfolio_allocation_is_a_complete_convex_qp_teaching_case() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "portfolio-allocation")

    assert case["problem_archetype_id"] == "PA018"
    assert len(case["question_answers"]) == 12
    assert case["question_answers"]["Q11"] == "lp_qp_conic"
    assert case["map_node_id"] == "answer:Q11:lp_qp_conic"
    assert {item["method_id"] for item in case["candidate_methods"]} == {"MF_LP_QP_CONIC"}
    ast.parse(case["python_example"])
    assert "np.array" in case["python_example"]
    assert "cp.quad_form" in case["python_example"]
    assert "$\\gamma=2$" in case["objective"]
    assert "held-out期間" in case["practical_notes"]
    assert "将来収益" in case["limitations"][1]
