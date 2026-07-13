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
    for case in fixture["cases"]:
        result = engine.recommend(RecommendationRequest.model_validate(case["request"]))
        assert recommendation_projection(result) == case["expected"], case["case_id"]
