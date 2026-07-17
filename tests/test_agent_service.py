from __future__ import annotations

import pytest

from optimization_compass.agent_service import AgentService
from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import RecommendationRequest


def test_agent_service_preserves_the_canonical_recommendation_result() -> None:
    service = AgentService()
    request = RecommendationRequest(
        answers={"Q01": ["binary"], "Q04": ["logical_or_combinatorial"]}
    )

    via_service = service.recommend_methods(request)
    direct = RecommendationEngine(service.repository).recommend(request)

    assert via_service == direct
    assert "M_CP_SAT" in {
        item.entity_id
        for item in [*via_service.first_choices, *via_service.conditional_choices]
    }


def test_agent_service_explanation_returns_stable_ids_not_only_prose() -> None:
    service = AgentService()
    request = RecommendationRequest(
        answers={"Q01": ["continuous"], "Q04": ["nonlinear"]}
    )

    result = service.recommend_methods(request)
    explanation = service.explain_recommendation(request)

    assert explanation.dataset_version == result.dataset_version
    assert explanation.answered_question_count == result.answered_question_count
    assert explanation.fired_rule_ids == tuple(sorted({item.rule_id for item in result.trace}))
    assert explanation.source_ids == tuple(
        sorted({source_id for item in result.trace for source_id in item.source_ids})
    )
    assert explanation.excluded_method_ids == tuple(
        sorted(item.entity_id for item in result.excluded_methods)
    )


def test_agent_capabilities_are_read_only_and_keep_unknown_explicit() -> None:
    service = AgentService()
    capabilities = service.get_capabilities()
    questions = service.list_diagnose_questions("ja")

    assert capabilities.read_only is True
    assert capabilities.recommendation_authority == "deterministic_rule_engine"
    assert "recommend_methods" in capabilities.operations
    assert any("unknown" in item["allowed_answers"] for item in questions)
    assert any("Unknown" in limitation for limitation in capabilities.limitations)


def test_agent_entity_lookup_uses_existing_repository_identity() -> None:
    service = AgentService()

    method = service.get_entity("method", "M_CP_SAT")
    assert method["method_id"] == "M_CP_SAT"

    with pytest.raises(LookupError, match="method not found"):
        service.get_entity("method", "M_DOES_NOT_EXIST")
