from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_ec020_declares_the_direct_collocation_flagship_formulation() -> None:
    payload = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in payload["cases"] if item["case_id"] == "EC020")

    assert [item["method_id"] for item in case["candidate_methods"]] == ["M_DIRECT_COLLOCATION"]
    assert "dynamics defect" in case["candidate_methods"][0]["reason"]
    assert "mesh（knot）数 $N=20$" in case["variable_domain"]
    assert "decision object" in case["decision_variables"]
    assert "dynamics defect" in case["constraints"]
    assert "x_0=x_{init}" in case["constraints"]
    assert "x_N=x_{goal}" in case["constraints"]
    assert "path制約" in case["constraints"]
    assert "max dynamics defect" in case["practical_notes"]
    assert "feasibility tolerance" in case["practical_notes"]
    assert "再構成" in case["practical_notes"]
    assert "連続時間の安全性" in case["limitations"][0]


def test_ec020_generated_journey_keeps_the_existing_direct_collocation_reading_link() -> None:
    payload = json.loads(
        (ROOT / "site/public/data/learning-journeys.json").read_text(encoding="utf-8")
    )
    journey = next(item for item in payload["journeys"] if item["case_id"] == "EC020")

    assert "direct-collocation" in journey["content_ids"]
