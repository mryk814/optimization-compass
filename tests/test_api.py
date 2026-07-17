import pytest
from fastapi.testclient import TestClient

from optimization_compass import api as api_module
from optimization_compass.api import app
from optimization_compass.web import (
    CANONICAL_ATLAS_URL,
    CANONICAL_BROWSER_UI_FIRST_VERSION,
    LEGACY_BROWSER_UI_LAST_VERSION,
)

client = TestClient(app)


def test_health() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_capabilities_expose_versioned_read_only_service_metadata() -> None:
    response = client.get("/v1/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["dataset_version"]
    assert body["metadata"]["non_guarantee"]
    assert body["capabilities"]["read_only"] is True


def test_questions() -> None:
    response = client.get("/v1/questions")
    assert response.status_code == 200
    assert len(response.json()) >= 12


def test_questions_use_the_shared_service_without_changing_the_public_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = api_module.service.list_diagnose_questions
    calls: list[str] = []

    def tracked(*, language: str, expected_dataset_version: str | None = None):
        calls.append(language)
        return original(
            language=language,
            expected_dataset_version=expected_dataset_version,
        )

    monkeypatch.setattr(api_module.service, "list_diagnose_questions", tracked)

    response = client.get("/v1/questions?language=en")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert calls == ["en"]


def test_recommendations() -> None:
    response = client.post(
        "/v1/recommendations",
        json={"answers": {"Q01": ["binary"], "Q04": ["logical_or_combinatorial"]}},
    )
    assert response.status_code == 200
    body = response.json()
    returned = {item["entity_id"] for item in body["first_choices"] + body["conditional_choices"]}
    assert "M_CP_SAT" in returned


def test_recommendations_use_the_shared_service_without_changing_the_public_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = api_module.service.recommend_methods
    calls: list[object] = []

    def tracked(payload: object, *, expected_dataset_version: str | None = None):
        calls.append(payload)
        return original(
            payload,  # type: ignore[arg-type]
            expected_dataset_version=expected_dataset_version,
        )

    monkeypatch.setattr(api_module.service, "recommend_methods", tracked)

    response = client.post(
        "/v1/recommendations",
        json={"answers": {"Q01": ["binary"], "Q04": ["logical_or_combinatorial"]}},
    )

    assert response.status_code == 200
    assert "metadata" not in response.json()
    assert len(calls) == 1


def test_invalid_answer_returns_422() -> None:
    response = client.post("/v1/recommendations", json={"answers": {"Q01": ["banana"]}})
    assert response.status_code == 422


def test_root_is_a_static_migration_landing_page_for_the_canonical_atlas() -> None:
    response = client.get("/?legacy-diagnosis=1")

    assert response.status_code == 200
    assert response.headers["link"] == f'<{CANONICAL_ATLAS_URL}>; rel="canonical"'
    assert 'data-browser-role="service-landing"' in response.text
    assert f'href="{CANONICAL_ATLAS_URL}"' in response.text
    assert 'href="/docs"' in response.text
    assert 'href="/openapi.json"' in response.text
    assert 'href="/healthz"' in response.text
    assert LEGACY_BROWSER_UI_LAST_VERSION in response.text
    assert CANONICAL_BROWSER_UI_FIRST_VERSION in response.text


def test_root_does_not_duplicate_the_atlas_diagnosis_ui_or_copy_contract() -> None:
    response = client.get("/")

    assert "<form" not in response.text
    assert "/v1/questions" not in response.text
    assert "/v1/recommendations" not in response.text
    assert "ANSWER_LABELS" not in response.text
    assert "<button" not in response.text


def test_rest_api_and_openapi_remain_available_after_browser_ui_migration() -> None:
    schema = client.get("/openapi.json")

    assert schema.status_code == 200
    paths = schema.json()["paths"]
    assert "/v1/capabilities" in paths
    assert "/v1/questions" in paths
    assert "/v1/recommendations" in paths
    assert "/v1/methods/{method_id}" in paths
    assert "/v1/implementations/{implementation_id}" in paths
    assert "/v1/sources/{source_id}" in paths
    assert "/v1/data/verify" in paths
    assert "/healthz" in paths
