from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from optimization_compass.db import KnowledgeRepository
from optimization_compass.engine import RecommendationEngine
from optimization_compass.models import Question, RecommendationRequest, RecommendationResponse

AgentOperationName = Literal[
    "get_capabilities",
    "list_diagnose_questions",
    "recommend_methods",
]
SupportedLanguage = Literal["ja", "en"]

AGENT_SERVICE_CONTRACT_VERSION: Literal["1.0.0"] = "1.0.0"
AGENT_SERVICE_ATTRIBUTION = (
    "Optimization Compass structured data, CC BY 4.0; preserve cited source IDs and "
    "verify important decisions against the sources and the real problem."
)
AGENT_SERVICE_NON_GUARANTEE = (
    "This guidance is not a solver result and does not guarantee optimality, feasibility, safety, "
    "or fitness for a particular use."
)


class AgentServiceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AgentServiceMetadata(AgentServiceModel):
    contract_version: Literal["1.0.0"] = AGENT_SERVICE_CONTRACT_VERSION
    dataset_version: str = Field(min_length=1)
    attribution: str = AGENT_SERVICE_ATTRIBUTION
    non_guarantee: str = AGENT_SERVICE_NON_GUARANTEE


class AgentToolDescriptor(AgentServiceModel):
    name: AgentOperationName
    read_only: Literal[True] = True
    description: str = Field(min_length=1)


class AgentCapabilities(AgentServiceModel):
    read_only: Literal[True] = True
    recommendation_authority: Literal["deterministic_rule_engine"] = "deterministic_rule_engine"
    unknown_policy: Literal["preserve"] = "preserve"
    tools: tuple[AgentToolDescriptor, ...]


class AgentCapabilitiesResponse(AgentServiceModel):
    metadata: AgentServiceMetadata
    capabilities: AgentCapabilities


class DiagnoseQuestionsResponse(AgentServiceModel):
    metadata: AgentServiceMetadata
    questions: tuple[Question, ...]


class AgentRecommendationResponse(AgentServiceModel):
    metadata: AgentServiceMetadata
    recommendation: RecommendationResponse


class DatasetVersionMismatch(ValueError):
    """Raised when a caller pins a dataset version different from the active authority."""


class UnsupportedLanguage(ValueError):
    """Raised when a caller requests a language outside the public service contract."""


class DeterministicGuidanceService:
    """Transport-independent, read-only access to canonical deterministic guidance.

    Recommendation authority remains in ``RecommendationEngine``. Returned text is serialized data,
    never an instruction to execute code, access a URL, or mutate repository state.
    """

    def __init__(self, repository: KnowledgeRepository | None = None) -> None:
        self._repository = repository or KnowledgeRepository()
        self._engine = RecommendationEngine(self._repository)

    @property
    def dataset_version(self) -> str:
        return str(self._repository.latest_release()["version"])

    def get_capabilities(
        self, *, expected_dataset_version: str | None = None
    ) -> AgentCapabilitiesResponse:
        self._require_dataset_version(expected_dataset_version)
        return AgentCapabilitiesResponse(
            metadata=self._metadata(),
            capabilities=AgentCapabilities(
                tools=(
                    AgentToolDescriptor(
                        name="get_capabilities",
                        description=(
                            "Return versioned read-only service capabilities; operations do not "
                            "execute solvers, code, plugins, SQL, or remote URLs."
                        ),
                    ),
                    AgentToolDescriptor(
                        name="list_diagnose_questions",
                        description=(
                            "Return canonical Diagnose questions and allowed answer states as "
                            "untrusted serialized data without rewriting unknown values."
                        ),
                    ),
                    AgentToolDescriptor(
                        name="recommend_methods",
                        description=(
                            "Return the canonical deterministic recommendation and evidence trail; "
                            "this is guidance, not a solver result or guarantee of optimality, "
                            "feasibility, or safety."
                        ),
                    ),
                )
            ),
        )

    def list_diagnose_questions(
        self,
        *,
        language: str = "ja",
        expected_dataset_version: str | None = None,
    ) -> DiagnoseQuestionsResponse:
        self._require_dataset_version(expected_dataset_version)
        supported_language = self._require_language(language)
        rows = self._repository.questions(supported_language)
        return DiagnoseQuestionsResponse(
            metadata=self._metadata(),
            questions=tuple(Question.model_validate(row) for row in rows),
        )

    def recommend_methods(
        self,
        payload: Mapping[str, Any] | RecommendationRequest,
        *,
        expected_dataset_version: str | None = None,
    ) -> AgentRecommendationResponse:
        self._require_dataset_version(expected_dataset_version)
        request = (
            payload
            if isinstance(payload, RecommendationRequest)
            else RecommendationRequest.model_validate(dict(payload))
        )
        recommendation = self._engine.recommend(request)
        return AgentRecommendationResponse(
            metadata=self._metadata(),
            recommendation=recommendation,
        )

    def _metadata(self) -> AgentServiceMetadata:
        return AgentServiceMetadata(dataset_version=self.dataset_version)

    def _require_dataset_version(self, expected: str | None) -> None:
        if expected is not None and expected != self.dataset_version:
            raise DatasetVersionMismatch(
                f"requested dataset {expected} does not match active dataset {self.dataset_version}"
            )

    @staticmethod
    def _require_language(language: str) -> SupportedLanguage:
        if language not in {"ja", "en"}:
            raise UnsupportedLanguage("language must be ja or en")
        return cast(SupportedLanguage, language)
