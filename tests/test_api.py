from fastapi.testclient import TestClient

from optimization_compass.api import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_questions() -> None:
    response = client.get("/v1/questions")
    assert response.status_code == 200
    assert len(response.json()) >= 12


def test_recommendations() -> None:
    response = client.post(
        "/v1/recommendations",
        json={"answers": {"Q01": ["binary"], "Q04": ["logical_or_combinatorial"]}},
    )
    assert response.status_code == 200
    body = response.json()
    returned = {item["entity_id"] for item in body["first_choices"] + body["conditional_choices"]}
    assert "M_CP_SAT" in returned


def test_invalid_answer_returns_422() -> None:
    response = client.post("/v1/recommendations", json={"answers": {"Q01": ["banana"]}})
    assert response.status_code == 422
