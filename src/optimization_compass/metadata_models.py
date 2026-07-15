from __future__ import annotations

from collections.abc import Hashable, Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonBlank = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
SupportStatus = Literal["supported", "unsupported", "unknown", "not_applicable"]


class MetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ViewFilterGroupSeed(MetadataModel):
    group_id: NonBlank
    label_ja: NonBlank
    label_en: NonBlank
    question_ids: list[NonBlank] = Field(default_factory=list)
    feature_ids: list[NonBlank] = Field(default_factory=list)
    method_ids: list[NonBlank] = Field(default_factory=list)
    alternative_ids: list[NonBlank] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_selectors(self) -> ViewFilterGroupSeed:
        selectors = [
            *self.question_ids,
            *self.feature_ids,
            *self.method_ids,
            *self.alternative_ids,
        ]
        if not selectors:
            raise ValueError("view filter group requires at least one canonical selector")
        for name, values in (
            ("question_ids", self.question_ids),
            ("feature_ids", self.feature_ids),
            ("method_ids", self.method_ids),
            ("alternative_ids", self.alternative_ids),
        ):
            _require_unique(values, name)
        return self


class ViewFilterPolicySeed(MetadataModel):
    mode: Literal["authored_groups"]
    groups: list[ViewFilterGroupSeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_groups(self) -> ViewFilterPolicySeed:
        _require_unique([group.group_id for group in self.groups], "view filter group IDs")
        selectors = [
            (selector_type, selector_id)
            for group in self.groups
            for selector_type, selector_ids in (
                ("question", group.question_ids),
                ("feature", group.feature_ids),
                ("method", group.method_ids),
                ("alternative", group.alternative_ids),
            )
            for selector_id in selector_ids
        ]
        _require_unique(selectors, "view filter selectors")
        return self


class ViewPresetSeed(MetadataModel):
    preset_id: NonBlank
    view_id: NonBlank
    family: Literal["semantic_tree", "algorithm_theater", "comparison"]
    name_ja: NonBlank
    name_en: NonBlank
    description_ja: NonBlank
    description_en: NonBlank
    root_support_status: SupportStatus
    root_entity_type: Literal["problem", "method", "view_preset"] | None
    root_entity_id: NonBlank | None
    axis: NonBlank
    relation_types: list[NonBlank] = Field(min_length=1)
    max_depth: int = Field(ge=1)
    filter_policy: ViewFilterPolicySeed
    limitations_ja: NonBlank
    limitations_en: NonBlank
    focus_fallback_entity_types: list[NonBlank] = Field(min_length=1)
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_conditionals(self) -> ViewPresetSeed:
        has_root = self.root_entity_type is not None and self.root_entity_id is not None
        if (self.root_support_status == "supported") != has_root:
            raise ValueError(
                "supported root requires both root entity fields; other states forbid them"
            )
        _require_unique(self.relation_types, "relation_types")
        _require_unique(self.focus_fallback_entity_types, "focus_fallback_entity_types")
        _require_unique(self.source_ids, "source_ids")
        return self


class VisualizationProfileSeed(MetadataModel):
    profile_id: NonBlank
    method_id: NonBlank
    family: Literal["simplex_2d", "first_order_trajectory_2d"]
    support_status: SupportStatus
    min_dimension: int = Field(ge=1)
    max_dimension: int = Field(ge=1)
    generator_id: NonBlank
    implementation_status: SupportStatus
    implementation_id: NonBlank | None
    state_fields: list[NonBlank] = Field(min_length=1)
    event_types: list[NonBlank] = Field(min_length=1)
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_conditionals(self) -> VisualizationProfileSeed:
        if self.max_dimension < self.min_dimension:
            raise ValueError("max_dimension must be >= min_dimension")
        if (self.implementation_status == "supported") != (self.implementation_id is not None):
            raise ValueError("supported implementation requires an ID; other states forbid one")
        for name, values in (
            ("state_fields", self.state_fields),
            ("event_types", self.event_types),
            ("source_ids", self.source_ids),
        ):
            _require_unique(values, name)
        return self


class DemoScenarioSeed(MetadataModel):
    scenario_id: NonBlank
    method_id: NonBlank
    profile_id: NonBlank
    problem_instance_id: NonBlank
    name_ja: NonBlank
    name_en: NonBlank
    initial_point: list[float] = Field(min_length=1)
    parameters: dict[str, object]
    stopping: dict[str, object]
    seed_status: Literal["fixed", "not_applicable", "unknown"]
    seed_value: int | None
    budget: int = Field(gt=0)
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_seed(self) -> DemoScenarioSeed:
        if (self.seed_status == "fixed") != (self.seed_value is not None):
            raise ValueError("fixed seed requires a value; other states forbid one")
        return self


class ComparisonSetSeed(MetadataModel):
    comparison_set_id: NonBlank
    problem_instance_id: NonBlank
    name_ja: NonBlank
    name_en: NonBlank
    initial_point: list[float] = Field(min_length=1)
    seed_status: Literal["fixed", "not_applicable", "unknown"]
    seed_value: int | None
    budget: int = Field(gt=0)
    stopping: dict[str, object]
    synchronization: Literal["oracle_evaluations"]
    fairness_note: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_seed(self) -> ComparisonSetSeed:
        if (self.seed_status == "fixed") != (self.seed_value is not None):
            raise ValueError("fixed seed requires a value; other states forbid one")
        return self


class ComparisonSetMemberSeed(MetadataModel):
    comparison_set_id: NonBlank
    member_id: NonBlank
    method_id: NonBlank
    profile_id: NonBlank
    label: NonBlank
    display_order: int = Field(ge=1)
    parameters: dict[str, object]


class LearningEdgeSeed(MetadataModel):
    edge_id: NonBlank
    source_type: Literal[
        "method",
        "problem",
        "feature",
        "case",
        "implementation",
        "scenario",
        "comparison",
        "view_preset",
    ]
    source_id: NonBlank
    target_type: Literal[
        "method",
        "problem",
        "feature",
        "case",
        "implementation",
        "scenario",
        "comparison",
        "view_preset",
    ]
    target_id: NonBlank
    relation: Literal[
        "prerequisite_for",
        "next_step",
        "contrast_with",
        "special_case_of",
        "generalizes",
        "applied_in",
        "common_misconception_for",
        "see_visualization",
        "see_comparison",
        "see_case",
        "implemented_by",
    ]
    rationale: NonBlank
    difficulty: Literal["beginner", "intermediate", "advanced", "all"]
    audience: Literal["learner", "practitioner", "researcher", "all"]
    display_order: int = Field(ge=1)
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank
    status: Literal["current", "deprecated", "draft"]

    @model_validator(mode="after")
    def reject_self_edge(self) -> LearningEdgeSeed:
        if (self.source_type, self.source_id) == (self.target_type, self.target_id):
            raise ValueError("learning edge cannot reference itself")
        return self


class TerminologyAliasSeed(MetadataModel):
    term_id: NonBlank
    target_type: Literal["method", "problem", "feature", "implementation"]
    target_id: NonBlank
    label_ja: NonBlank
    label_en: NonBlank
    abbreviations: list[NonBlank] = Field(default_factory=list)
    synonyms: list[NonBlank] = Field(default_factory=list)
    domain_terms: list[NonBlank] = Field(default_factory=list)
    misspellings: list[NonBlank] = Field(default_factory=list)
    deprecated_terms: list[NonBlank] = Field(default_factory=list)
    disambiguation_note: NonBlank | None = None
    locale: NonBlank
    rationale: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_terms(self) -> TerminologyAliasSeed:
        groups = (
            self.abbreviations,
            self.synonyms,
            self.domain_terms,
            self.misspellings,
            self.deprecated_terms,
        )
        normalized = [value.casefold().strip() for group in groups for value in group]
        if len(normalized) != len(set(normalized)):
            raise ValueError("terminology terms must be unique within a canonical entity")
        return self


class LearningCoverageExpectationSeed(MetadataModel):
    expectation_id: NonBlank
    subject_type: Literal["method", "problem", "feature_family"]
    subject_id: NonBlank
    purpose: Literal[
        "mechanism",
        "comparison",
        "failure_contrast",
        "sensitivity",
        "application_result",
        "schematic",
    ]
    artifact_kind: Literal[
        "executable_trace", "schematic_animation", "static_diagram", "result_visualization"
    ]
    renderer_family: NonBlank
    applicability: Literal["expected", "not_applicable"]
    rationale: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank
    slice_id: NonBlank | None = None


class LearningSlicePrioritySeed(MetadataModel):
    slice_id: NonBlank
    title_ja: NonBlank
    title_en: NonBlank
    classification_score: int = Field(ge=0, le=3)
    classification_reason: NonBlank
    misconception_score: int = Field(ge=0, le=3)
    misconception_reason: NonBlank
    visualization_score: int = Field(ge=0, le=3)
    visualization_reason: NonBlank
    demand_score: int = Field(ge=0, le=3)
    demand_reason: NonBlank
    proposed_scope: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank


class AtlasMetadataSeed(MetadataModel):
    view_presets: list[ViewPresetSeed] = Field(min_length=1)
    method_visualization_profiles: list[VisualizationProfileSeed] = Field(min_length=1)
    demo_scenarios: list[DemoScenarioSeed] = Field(min_length=1)
    comparison_sets: list[ComparisonSetSeed] = Field(min_length=1)
    comparison_set_members: list[ComparisonSetMemberSeed] = Field(min_length=1)
    learning_edges: list[LearningEdgeSeed] = Field(min_length=1)
    terminology_aliases: list[TerminologyAliasSeed] = Field(min_length=30)
    learning_coverage_expectations: list[LearningCoverageExpectationSeed] = Field(min_length=1)
    learning_slice_priorities: list[LearningSlicePrioritySeed] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_closures(self) -> AtlasMetadataSeed:
        collections = (
            (self.view_presets, "preset_id"),
            (self.method_visualization_profiles, "profile_id"),
            (self.demo_scenarios, "scenario_id"),
            (self.comparison_sets, "comparison_set_id"),
            (self.learning_edges, "edge_id"),
            (self.terminology_aliases, "term_id"),
            (self.learning_coverage_expectations, "expectation_id"),
            (self.learning_slice_priorities, "slice_id"),
        )
        for rows, key in collections:
            _require_unique([str(getattr(row, key)) for row in rows], key)

        profiles = {(row.method_id, row.profile_id) for row in self.method_visualization_profiles}
        comparisons = {row.comparison_set_id for row in self.comparison_sets}
        for scenario in self.demo_scenarios:
            if (scenario.method_id, scenario.profile_id) not in profiles:
                raise ValueError(f"scenario profile does not resolve: {scenario.scenario_id}")
        member_keys: set[tuple[str, str]] = set()
        member_orders: set[tuple[str, int]] = set()
        member_methods: set[tuple[str, str]] = set()
        for member in self.comparison_set_members:
            if member.comparison_set_id not in comparisons:
                raise ValueError(f"comparison does not resolve: {member.comparison_set_id}")
            if (member.method_id, member.profile_id) not in profiles:
                raise ValueError(f"member profile does not resolve: {member.member_id}")
            member_key = (member.comparison_set_id, member.member_id)
            if member_key in member_keys:
                raise ValueError(f"duplicate member: {member_key}")
            member_keys.add(member_key)
            order_key = (member.comparison_set_id, member.display_order)
            if order_key in member_orders:
                raise ValueError(f"duplicate member order: {order_key}")
            member_orders.add(order_key)
            method_key = (member.comparison_set_id, member.method_id)
            if method_key in member_methods:
                raise ValueError(f"duplicate member method: {method_key}")
            member_methods.add(method_key)
        edge_keys = [
            (row.source_type, row.source_id, row.target_type, row.target_id, row.relation)
            for row in self.learning_edges
        ]
        _require_unique(edge_keys, "learning edge")
        alias_targets = [(row.target_type, row.target_id) for row in self.terminology_aliases]
        _require_unique(alias_targets, "terminology alias target")
        owners: dict[str, list[TerminologyAliasSeed]] = {}
        for row in self.terminology_aliases:
            terms = [
                row.label_ja,
                row.label_en,
                *row.abbreviations,
                *row.synonyms,
                *row.domain_terms,
                *row.misspellings,
                *row.deprecated_terms,
            ]
            for term in terms:
                owners.setdefault(term.casefold().replace(" ", ""), []).append(row)
        ambiguous = [
            term
            for term, rows in owners.items()
            if len({(row.target_type, row.target_id) for row in rows}) > 1
            and any(row.disambiguation_note is None for row in rows)
        ]
        if ambiguous:
            raise ValueError(
                "ambiguous terminology requires disambiguation: " + ", ".join(sorted(ambiguous))
            )
        expectation_keys = [
            (row.subject_type, row.subject_id, row.purpose, row.artifact_kind, row.renderer_family)
            for row in self.learning_coverage_expectations
        ]
        _require_unique(expectation_keys, "learning coverage expectation")
        slice_ids = {row.slice_id for row in self.learning_slice_priorities}
        for expectation in self.learning_coverage_expectations:
            if expectation.slice_id is not None and expectation.slice_id not in slice_ids:
                raise ValueError(f"coverage slice does not resolve: {expectation.expectation_id}")
        return self


def _require_unique(values: Sequence[Hashable], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} values are not allowed")
