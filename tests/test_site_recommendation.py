from __future__ import annotations

import json
from pathlib import Path

from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import RecommendationRequest
from optimization_compass.site_recommendation import (
    SiteData,
    build_site_data,
    recommendation_projection,
)


def test_site_data_is_complete_and_deterministic(repository: object) -> None:
    first = build_site_data(repository)
    second = build_site_data(repository)

    assert isinstance(first, SiteData)
    assert first == second
    assert first.contract_version == "1.0.0"
    assert first.dataset_version == "0.2.0"
    assert len(first.questions) == 12
    assert len(first.rules) == 78
    assert first.questions[0].choices[2].value == "binary"
    assert first.questions[0].choices[2].label_ja == "0-1"


def test_site_export_contains_recommendation_artifact(tmp_path: Path, repository: object) -> None:
    from optimization_compass.site_export import export_site_data

    export_site_data(tmp_path, repository)
    artifact = tmp_path / "recommendation/site-data.json"
    assert artifact.is_file()
    SiteData.model_validate_json(artifact.read_bytes())


def test_shared_recommendation_cases_match_python_engine(
    engine: RecommendationEngine,
) -> None:
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/recommendation_cases.json").read_text(encoding="utf-8")
    )
    assert fixture["fixture_version"] == "1.0.0"
    assert fixture["dataset_version"] == "0.2.0"
    assert len(fixture["cases"]) == 9
    smooth = next(case for case in fixture["cases"] if case["case_id"] == "smooth_continuous")
    assert smooth["request"]["max_methods"] == 5
    assert smooth["request"]["max_implementations_per_method"] == 4
    assert "implementation_ids" in smooth["expected"]["first_choices"][0]
    assert "reasons" in smooth["expected"]["first_choices"][0]
    assert "warnings" in smooth["expected"]["first_choices"][0]
    assert len(smooth["expected"]["first_choices"]) == 5
    smooth_first = {choice["entity_id"]: choice for choice in smooth["expected"]["first_choices"]}
    assert smooth_first["M_LBFGS"]["implementation_ids"] == [
        "I_NLOPT",
        "I_OPTIMJL",
        "I_PETSC_TAO",
        "I_PYTORCH_OPTIM",
    ]
    assert smooth_first["M_INTERIOR_POINT_NLP"]["implementation_ids"] == [
        "I_CASADI",
        "I_DRAKE",
        "I_IPOPT",
        "I_KNITRO",
    ]
    for case in fixture["cases"]:
        result = engine.recommend(RecommendationRequest.model_validate(case["request"]))
        assert recommendation_projection(result) == case["expected"], case["case_id"]
