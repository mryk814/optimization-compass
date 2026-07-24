from __future__ import annotations

import ast
import json
from pathlib import Path


def test_ec025_has_a_complete_repeated_mpc_qp_teaching_instance() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "EC025")

    assert case["problem_archetype_id"] == "PA043"
    assert len(case["question_answers"]) == 12
    assert case["question_answers"]["Q12"] == "online_or_realtime"
    assert case["map_node_id"] == "answer:Q12:online_or_realtime"
    assert {item["method_id"] for item in case["candidate_methods"]} == {"M_ADMM_QP"}
    assert {"S012", "S043", "S076"} <= set(case["source_ids"])
    ast.parse(case["python_example"])
    assert "solver.update" in case["python_example"]
    assert "solver.warm_start" in case["python_example"]
    assert "$N=4$" in case["variable_domain"]
    assert "deadline miss率" in case["practical_notes"]
    assert "100Hz" in case["limitations"][1]
    assert "closed-loop試験" in case["limitations"][1]
