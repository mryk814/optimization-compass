from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from optimization_compass.db import KnowledgeRepository
from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import RecommendationRequest, RecommendationResponse

AgentEntityType = Literal["method", "implementation", "source"]
AgentOperation = Literal[
    "get_capabilities",
    "list_diagnose_questions",
    "recommend_methods",
    "explain_recommendation",
    "get_entity",
]


class AgentContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AgentCapabilities(AgentContractModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    read_only: Literal[True] = True
    recommendation_authority: Literal["deterministic_rule_engine"] = (
        "deterministic_rule_engine"
    )
    supported_languages: tuple[Literal["ja", "en"], ...] = ("ja", "en")
    operations: tuple[AgentOperation, ...] = (
        "get_capabilities",
        "list_diagnose_questions",
        "recommend_methods",
        "explain_recommendation",
        "get_entity",
    )
    attribution: str = Field(min_length=1)
    limitations: tuple[str, ...]


class RecommendationExplanation(AgentContractModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    answered_question_count: int = Field(ge=0)
    fired_rule_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    excluded_method_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    disclaimer: str = Field(min_length=1)


class AgentService:
    """Protocol-neutral, read-only boundary for CLI, REST, and a future MCP adapter."""

    def __init__(
        self,
        repository: KnowledgeRepository | None = None,
        engine: RecommendationEngine | None = None,
    ) -> None:
        self.repository = repository or KnowledgeRepository()
        self.engine = engine or RecommendationEngine(self.repository)

    def get_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            dataset_version=self.repository.dataset_version(),
            attribution=(
                "Optimization Compass structured data, CC BY 4.0; "
                "https://github.com/mryk814/optimization-compass"
            ),
            limitations=(
                "Decision support only; numerical performance, safety, and optimality are not guaranteed.",
                "Unknown answers remain unknown and are never silently converted to yes or no.",
                "Excluded, conditional, and candidate dispositions must remain distinct.",
                "The service does not execute arbitrary remote solvers or user-supplied code.",
            ),
        )

    def list_diagnose_questions(self, language: Literal["ja", "en"] = "ja") -> list[dict[str, Any]]:
        return self.repository.questions(language)

    def recommend_methods(self, request: RecommendationRequest) -> RecommendationResponse:
        return self.engine.recommend(request)

    def explain_recommendation(
        self, request: RecommendationRequest
    ) -> RecommendationExplanation:
        response = self.recommend_methods(request)
        return RecommendationExplanation(
            dataset_version=response.dataset_version,
            answered_question_count=response.answered_question_count,
            fired_rule_ids=tuple(sorted({item.rule_id for item in response.trace})),
            source_ids=tuple(
                sorted(
                    {
                        source_id
                        for item in response.trace
                        for source_id in item.source_ids
                    }
                )
            ),
            excluded_method_ids=tuple(
                sorted(item.entity_id for item in response.excluded_methods)
            ),
            warnings=tuple(response.warnings),
            disclaimer=response.disclaimer,
        )

    def get_entity(self, entity_type: AgentEntityType, entity_id: str) -> dict[str, Any]:
        loader = {
            "method": self.repository.method,
            "implementation": self.repository.implementation,
            "source": self.repository.source,
        }[entity_type]
        row = loader(entity_id)
        if row is None:
            raise LookupError(f"{entity_type} not found: {entity_id}")
        return row

    def verify_data(self) -> dict[str, Any]:
        return self.repository.verify()
