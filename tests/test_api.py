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


def test_browser_copy_preserves_canonical_values() -> None:
    from optimization_compass.web import HTML

    assert "連続値（continuous）" in HTML
    assert "0/1の二値（binary）" in HTML
    assert "この質問で確認すること：" in HTML
    assert "一致した判断ルール" in HTML
    assert "主な実装例" in HTML
    assert "適用された判断ルール" in HTML
    assert 'value="${esc(a)}"' in HTML
