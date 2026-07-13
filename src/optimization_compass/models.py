from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Question(BaseModel):
    question_id: str
    sequence: int
    question: str
    beginner_wording: str
    answer_type: Literal["single_choice", "multi_choice"]
    allowed_answers: list[str]
    why_asked: str
    required: bool
    confidence: str


class RecommendationRequest(BaseModel):
    answers: dict[str, list[str]] = Field(
        description="Question IDs mapped to one or more canonical answer values."
    )
    language: Literal["ja", "en"] = "ja"
    max_methods: int = Field(default=8, ge=1, le=30)
    max_implementations_per_method: int = Field(default=3, ge=0, le=10)

    @field_validator("answers", mode="before")
    @classmethod
    def normalize_answers(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        normalized: dict[str, list[str]] = {}
        for key, answer in value.items():
            if isinstance(answer, str):
                normalized[str(key)] = [answer]
            elif isinstance(answer, list):
                normalized[str(key)] = [str(item) for item in answer]
            else:
                raise ValueError(f"answer for {key} must be a string or list of strings")
        return normalized


class ImplementationSummary(BaseModel):
    implementation_id: str
    library_name: str
    solver_name: str
    language: str
    license: str
    maintenance_status: str
    last_release: str
    official_docs_url: str
    official_repo_url: str
    support_level: str
    notes: str


class EntityRecommendation(BaseModel):
    entity_id: str
    name: str
    name_en: str = ""
    summary: str = ""
    priority_band: Literal["first_choice", "conditional", "excluded", "alternative"]
    supporting_rule_count: int
    high_priority_rule_count: int = 0
    medium_priority_rule_count: int = 0
    reasons: list[str]
    warnings: list[str]
    source_ids: list[str]
    implementations: list[ImplementationSummary] = Field(default_factory=list)


class RuleTrace(BaseModel):
    rule_id: str
    question_id: str
    matched_answer: str
    action_type: str
    action_target_type: str
    action_target_ids: list[str]
    priority_effect: str
    explanation: str
    warnings: str
    source_ids: list[str]


class Followup(BaseModel):
    question_id: str
    explanation: str
    target_type: str
    target_ids: list[str]


class RecommendationResponse(BaseModel):
    alternatives_first: list[EntityRecommendation]
    first_choices: list[EntityRecommendation]
    conditional_choices: list[EntityRecommendation]
    excluded_methods: list[EntityRecommendation]
    candidate_problem_archetypes: list[EntityRecommendation]
    followups: list[Followup]
    warnings: list[str]
    trace: list[RuleTrace]
    answered_question_count: int
    dataset_version: str
    disclaimer: str


class VerificationResult(BaseModel):
    ok: bool
    foreign_key_violations: int
    failed_release_checks: int
    warning_release_checks: int
    total_release_checks: int
    dataset_version: str
    details: list[dict[str, Any]]
