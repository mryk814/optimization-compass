from __future__ import annotations

import ast
import json
from pathlib import Path


def test_shift_scheduling_uses_the_scheduling_archetype_and_explicit_hard_constraints() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "shift-scheduling")

    assert case["problem_archetype_id"] == "PA026"
    assert len(case["question_answers"]) == 12
    assert case["question_answers"]["Q11"] == "scheduling_routing"
    assert case["map_node_id"] == "answer:Q01:binary"
    assert {item["method_id"] for item in case["candidate_methods"]} == {"M_CP_SAT"}
    assert {item["method_id"] for item in case["conditional_methods"]} == {"MF_DISCRETE_EXACT"}
    assert {item["method_id"] for item in case["excluded_methods"]} == {"M_GRADIENT_DESCENT"}
    ast.parse(case["python_example"])
    assert "hard constraint" in case["objective"]
    assert "夜勤後の翌日日勤" in case["constraints"]
    assert "最適性は未証明" in case["practical_notes"]
    assert "実際の労働協約" in case["limitations"][0]
    assert "本人同意" in case["limitations"][1]
