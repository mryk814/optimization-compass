from __future__ import annotations

import ast
import json
from pathlib import Path


def test_ec021_connects_neural_training_without_overclaiming_the_quadratic_lesson() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "EC021")

    assert case["domain"] == "machine-learning"
    assert case["problem_archetype_id"] == "PA040"
    assert case["question_answers"]["Q05"] == "stochastic_gradient"
    assert case["map_node_id"] == "answer:Q05:stochastic_gradient"
    assert case["comparison_ids"] == ["COMPARE_GRADIENT_FAMILY"]
    assert {item["method_id"] for item in case["candidate_methods"]} == {"M_ADAMW"}
    assert {item["method_id"] for item in case["conditional_methods"]} == {"M_MOMENTUM_SGD"}
    assert {item["method_id"] for item in case["excluded_methods"]} == {"M_BFGS"}
    ast.parse(case["python_example"])
    assert "2次元の細長い二次関数" in case["practical_notes"]
    assert "画像dataやneural networkを学習していない" in case["practical_notes"]
    assert "順位を保証しない" in case["limitations"][1]
