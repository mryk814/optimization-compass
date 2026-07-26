from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gradient_divergence_lesson_belongs_to_the_minibatch_training_journey() -> None:
    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    comparisons = json.loads(
        (ROOT / "data/seeds/site_comparisons.json").read_text(encoding="utf-8")
    )

    case = next(item for item in gallery["cases"] if item["case_id"] == "EC021")
    comparison = next(
        item
        for item in comparisons["comparisons"]
        if item["comparison_id"] == "COMPARE_GRADIENT_DIVERGENCE"
    )
    family_comparison = next(
        item
        for item in comparisons["comparisons"]
        if item["comparison_id"] == "COMPARE_GRADIENT_FAMILY"
    )

    assert {
        "SCENARIO_GRADIENT_DESCENT_QUADRATIC_DIVERGENCE",
        "SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE",
        "SCENARIO_ADAM_QUADRATIC_DIVERGENCE",
    } <= set(case["visualization_ids"])
    assert "COMPARE_GRADIENT_DIVERGENCE" in case["comparison_ids"]
    assert comparison["journey_id"] == "EC021"
    assert comparison["case_id"] == "EC021"
    assert family_comparison["journey_id"] == "EC021"
    assert family_comparison["case_id"] == "EC021"
    assert comparison["ranking_eligible"] is False
    assert "一般的な順位付けには使用できません" in comparison["caveat"]
