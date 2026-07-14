from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from optimization_compass.db import KnowledgeRepository
from optimization_compass.models import EntityRecommendation, RecommendationResponse
from optimization_compass.site_export import _answer_labels, _required_display_text
from optimization_compass.view_spec import ContractModel

SITE_DATA_VERSION: Literal["1.0.0"] = "1.0.0"

ActionType = Literal[
    "promote_method",
    "exclude_method",
    "recommend_alternative",
    "include_problem",
    "ask_followup",
    "warn",
]
TargetType = Literal["method", "alternative", "problem", "feature"]
Priority = Literal["high", "medium", "candidate", "none"]


class SiteChoice(ContractModel):
    value: str = Field(min_length=1)
    label_ja: str = Field(min_length=1)
    label_en: str = Field(min_length=1)


class SiteQuestion(ContractModel):
    question_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    question_ja: str = Field(min_length=1)
    question_en: str = Field(min_length=1)
    beginner_wording: str = Field(min_length=1)
    answer_type: Literal["single_choice", "multi_choice"]
    allowed_answers: list[str] = Field(min_length=1)
    choices: list[SiteChoice] = Field(min_length=1)
    mapped_feature_id: str = Field(min_length=1)
    why_asked: str = Field(min_length=1)
    required: bool
    confidence: str = Field(min_length=1)
    source_ids: list[str]

    @model_validator(mode="after")
    def validate_choices(self) -> SiteQuestion:
        values = [choice.value for choice in self.choices]
        if values != self.allowed_answers:
            raise ValueError(f"choices do not match allowed_answers: {self.question_id}")
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate answer value: {self.question_id}")
        return self


class SiteRule(ContractModel):
    rule_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    answer_condition: str = Field(min_length=1)
    action_type: ActionType
    action_target_type: TargetType
    action_target_ids: list[str] = Field(min_length=1)
    priority_effect: Priority
    explanation: str
    warnings: str
    source_ids: list[str]


class SiteMethod(ContractModel):
    method_id: str = Field(min_length=1)
    name_ja: str = Field(min_length=1)
    name_en: str = Field(min_length=1)
    summary: str
    variable_types: str
    solution_scope: str
    optimality_certificate: str
    exactness: str
    reference_source_ids: list[str]


class SiteImplementation(ContractModel):
    implementation_id: str = Field(min_length=1)
    library_name: str
    solver_name: str
    language: str
    license: str
    maintenance_status: str
    last_release: str
    official_docs_url: str
    official_repo_url: str
    notes: str


class SiteMethodImplementation(ContractModel):
    method_id: str = Field(min_length=1)
    implementation_id: str = Field(min_length=1)
    support_level: str
    implementation_notes: str


class SiteAlternative(ContractModel):
    alternative_id: str = Field(min_length=1)
    name_ja: str = Field(min_length=1)
    name_en: str = Field(min_length=1)
    why_before_generic_optimization: str
    preferred_approach: str
    false_positive_warning: str
    source_ids: list[str]


class SiteProblem(ContractModel):
    problem_id: str = Field(min_length=1)
    name_ja: str = Field(min_length=1)
    name_en: str = Field(min_length=1)
    summary: str
    source_ids: list[str]


class SiteFeature(ContractModel):
    feature_id: str = Field(min_length=1)
    name_ja: str = Field(min_length=1)
    name_en: str = Field(min_length=1)
    definition: str
    source_ids: list[str]


class SiteFeatureValue(ContractModel):
    feature_id: str = Field(min_length=1)
    value_code: str = Field(min_length=1)
    label_ja: str = Field(min_length=1)
    label_en: str = Field(min_length=1)
    sort_order: int


class SiteSource(ContractModel):
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    supported_claim: str
    url: str


class SiteData(ContractModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    questions: list[SiteQuestion]
    rules: list[SiteRule]
    methods: list[SiteMethod]
    implementations: list[SiteImplementation]
    method_implementation_map: list[SiteMethodImplementation]
    alternatives: list[SiteAlternative]
    problems: list[SiteProblem]
    features: list[SiteFeature]
    feature_values: list[SiteFeatureValue]
    sources: list[SiteSource]

    @field_validator("questions", "rules", "methods")
    @classmethod
    def require_core_rows(cls, value: list[object]) -> list[object]:
        if not value:
            raise ValueError("SiteData core collections must not be empty")
        return value

    @model_validator(mode="after")
    def validate_references(self) -> SiteData:
        questions = _unique(self.questions, "question_id")
        methods = _unique(self.methods, "method_id")
        alternatives = _unique(self.alternatives, "alternative_id")
        problems = _unique(self.problems, "problem_id")
        features = _unique(self.features, "feature_id")
        implementations = _unique(self.implementations, "implementation_id")
        sources = _unique(self.sources, "source_id")
        _unique(self.rules, "rule_id")
        targets = {
            "method": methods,
            "alternative": alternatives,
            "problem": problems,
            "feature": features,
        }
        for question in self.questions:
            if question.mapped_feature_id not in features:
                raise ValueError(f"missing mapped feature: {question.mapped_feature_id}")
            _require_sources(question.source_ids, sources, question.question_id)
        for rule in self.rules:
            matched_question = questions.get(rule.question_id)
            if (
                matched_question is None
                or rule.answer_condition not in matched_question.allowed_answers
            ):
                raise ValueError(f"non-canonical rule condition: {rule.rule_id}")
            missing = set(rule.action_target_ids) - set(targets[rule.action_target_type])
            if missing:
                raise ValueError(f"missing rule targets for {rule.rule_id}: {sorted(missing)}")
            _require_sources(rule.source_ids, sources, rule.rule_id)
        for collection, identifier in (
            (self.methods, "method_id"),
            (self.alternatives, "alternative_id"),
            (self.problems, "problem_id"),
            (self.features, "feature_id"),
        ):
            for item in collection:
                source_ids = (
                    item.reference_source_ids if isinstance(item, SiteMethod) else item.source_ids
                )
                _require_sources(source_ids, sources, str(getattr(item, identifier)))
        feature_value_keys: set[tuple[str, str]] = set()
        for feature_value in self.feature_values:
            key = (feature_value.feature_id, feature_value.value_code)
            if key in feature_value_keys:
                raise ValueError(f"duplicate feature value: {key}")
            feature_value_keys.add(key)
            if feature_value.feature_id not in features:
                raise ValueError(f"missing feature for value: {key}")
        seen_mappings: set[tuple[str, str]] = set()
        for mapping in self.method_implementation_map:
            key = (mapping.method_id, mapping.implementation_id)
            if key in seen_mappings:
                raise ValueError(f"duplicate method implementation mapping: {key}")
            seen_mappings.add(key)
            if mapping.method_id not in methods or mapping.implementation_id not in implementations:
                raise ValueError(f"broken method implementation mapping: {key}")
        return self


def build_site_data(repository: KnowledgeRepository) -> SiteData:
    release = repository.latest_release()
    generated_at = datetime.combine(
        date.fromisoformat(release["release_date"]), time.min, tzinfo=UTC
    )
    question_rows = repository.recommendation_questions()
    rule_rows = repository.recommendation_rules()
    target_ids = _targets(rule_rows)
    feature_ids = sorted(
        {str(row["mapped_feature_id"]) for row in question_rows} | target_ids["feature"]
    )
    features = repository.atlas_features(feature_ids)
    feature_values = repository.atlas_feature_values(feature_ids)
    feature_value_by_key = {
        (str(row["feature_id"]), str(row["value_code"])): row for row in feature_values
    }
    method_rows = repository.atlas_methods(sorted(target_ids["method"]))
    problem_rows = repository.atlas_problems(sorted(target_ids["problem"]))
    alternative_rows = [
        row
        for row in repository.atlas_alternatives()
        if str(row["alternative_id"]) in target_ids["alternative"]
    ]
    implementations, mappings = repository.recommendation_implementations(
        sorted(target_ids["method"])
    )
    source_ids = sorted(
        {
            str(source_id)
            for row in [
                *question_rows,
                *rule_rows,
                *features,
                *method_rows,
                *problem_rows,
                *alternative_rows,
            ]
            for source_id in row.get("source_ids", [])
        }
    )
    sources = repository.atlas_sources(source_ids)

    questions: list[SiteQuestion] = []
    for row in question_rows:
        feature_id = str(row["mapped_feature_id"])
        choices = []
        for value in row["allowed_answers"]:
            label_ja, label_en = _answer_labels(feature_id, str(value), feature_value_by_key)
            choices.append(SiteChoice(value=str(value), label_ja=label_ja, label_en=label_en))
        questions.append(SiteQuestion(**row, choices=choices))

    return SiteData(
        dataset_version=release["version"],
        generated_at=generated_at,
        questions=questions,
        rules=[SiteRule(**row) for row in rule_rows],
        methods=[
            SiteMethod(
                method_id=str(row["method_id"]),
                name_ja=_required_display_text(row.get("name_ja"), "method name_ja"),
                name_en=_required_display_text(row.get("name_en"), "method name_en"),
                summary=str(row.get("summary") or ""),
                variable_types=str(row.get("variable_types") or ""),
                solution_scope=str(row.get("solution_scope") or ""),
                optimality_certificate=str(row.get("optimality_certificate") or ""),
                exactness=str(row.get("exactness") or ""),
                reference_source_ids=[str(item) for item in row["source_ids"]],
            )
            for row in method_rows
        ],
        implementations=[SiteImplementation(**row) for row in implementations],
        method_implementation_map=[SiteMethodImplementation(**row) for row in mappings],
        alternatives=[
            SiteAlternative(
                **{**row, "false_positive_warning": str(row.get("false_positive_warning") or "")}
            )
            for row in alternative_rows
        ],
        problems=[SiteProblem(**row) for row in problem_rows],
        features=[SiteFeature(**row) for row in features],
        feature_values=[SiteFeatureValue(**row) for row in feature_values],
        sources=[SiteSource(**row) for row in sources],
    )


def recommendation_projection(result: RecommendationResponse) -> dict[str, Any]:
    def entities(items: list[EntityRecommendation]) -> list[dict[str, Any]]:
        return [
            {
                "entity_id": item.entity_id,
                "name": item.name,
                "priority_band": item.priority_band,
                "supporting_rule_count": item.supporting_rule_count,
                "high_priority_rule_count": item.high_priority_rule_count,
                "medium_priority_rule_count": item.medium_priority_rule_count,
                "reasons": item.reasons,
                "warnings": item.warnings,
                "source_ids": item.source_ids,
                "implementation_ids": [
                    implementation.implementation_id for implementation in item.implementations
                ],
            }
            for item in items
        ]

    return {
        "alternatives_first": entities(result.alternatives_first),
        "first_choices": entities(result.first_choices),
        "conditional_choices": entities(result.conditional_choices),
        "excluded_methods": entities(result.excluded_methods),
        "candidate_problem_archetypes": entities(result.candidate_problem_archetypes),
        "followups": [
            {
                "question_id": item.question_id,
                "explanation": item.explanation,
                "target_type": item.target_type,
                "target_ids": item.target_ids,
            }
            for item in result.followups
        ],
        "warnings": result.warnings,
        "trace": [item.model_dump(mode="json") for item in result.trace],
        "answered_question_count": result.answered_question_count,
        "dataset_version": result.dataset_version,
        "disclaimer": result.disclaimer,
    }


def _targets(rules: list[dict[str, Any]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {
        key: set() for key in ("method", "alternative", "problem", "feature")
    }
    for rule in rules:
        target_type = str(rule["action_target_type"])
        if target_type not in result:
            raise ValueError(f"unsupported recommendation target type: {target_type}")
        result[target_type].update(str(item) for item in rule["action_target_ids"])
    return result


def _unique(items: list[Any], attribute: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items:
        key = str(getattr(item, attribute))
        if key in result:
            raise ValueError(f"duplicate SiteData ID: {key}")
        result[key] = item
    return result


def _require_sources(source_ids: list[str], sources: dict[str, Any], owner: str) -> None:
    missing = set(source_ids) - set(sources)
    if missing:
        raise ValueError(f"missing sources for {owner}: {sorted(missing)}")
