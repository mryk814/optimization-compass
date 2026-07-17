from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonBlank = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
ComparisonMode = Literal[
    "method_contrast",
    "parameter_sensitivity",
    "initial_condition_sensitivity",
    "failure_contrast",
    "strategy_contrast",
    "result_tradeoff",
]
RendererFamily = Literal[
    "continuous_trajectory",
    "generic_metric_history",
    "search_tree",
    "surrogate_uncertainty",
    "feasible_region",
    "pareto_front",
]


class ComparisonModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Budget(ComparisonModel):
    metric: NonBlank
    value: int = Field(gt=0)


class MetricDefinition(ComparisonModel):
    metric_id: NonBlank
    label_ja: NonBlank
    direction: Literal["minimize", "maximize", "target", "none"]
    unit: NonBlank


class ComparisonArtifact(ComparisonModel):
    artifact_id: NonBlank
    artifact_kind: Literal["executable_trace", "result_visualization"]
    renderer_family: RendererFamily
    renderer_contract_version: NonBlank
    payload_path: NonBlank

    @model_validator(mode="after")
    def validate_artifact_kind(self) -> ComparisonArtifact:
        if (
            self.renderer_family
            in {
                "continuous_trajectory",
                "generic_metric_history",
                "search_tree",
                "surrogate_uncertainty",
                "feasible_region",
            }
            and self.artifact_kind != "executable_trace"
        ):
            raise ValueError(f"{self.renderer_family} requires an executable_trace artifact")
        if self.renderer_family == "pareto_front" and self.artifact_kind != "result_visualization":
            raise ValueError("pareto_front requires a result_visualization artifact")
        return self


class ComparisonMember(ComparisonModel):
    member_id: NonBlank
    role: NonBlank
    method_id: NonBlank
    scenario_id: NonBlank
    label_ja: NonBlank
    label_en: NonBlank
    parameters: dict[str, float | int | str | bool]
    budget: Budget
    artifact: ComparisonArtifact


class ComparisonSet(ComparisonModel):
    comparison_id: NonBlank
    canonical_url: NonBlank
    identity_status: Literal["canonical", "derived"]
    canonical_comparison_id: NonBlank
    aliases: list[NonBlank]
    mode: ComparisonMode
    journey_id: NonBlank
    case_id: NonBlank
    problem_definition_id: NonBlank
    problem_instance_id: NonBlank
    benchmark_context_id: NonBlank
    title_ja: NonBlank
    title_en: NonBlank
    comparison_question: NonBlank
    formulation_summary: NonBlank
    fixed_factors: list[NonBlank] = Field(min_length=1)
    changed_factors: list[NonBlank] = Field(min_length=1)
    seed_policy: NonBlank
    budget: Budget
    stopping_policy: NonBlank
    tuning_policy: NonBlank
    synchronization_axis: NonBlank
    metrics: list[MetricDefinition] = Field(min_length=1)
    comparability: Literal["comparable_with_caveat", "contrast_only", "not_comparable"]
    ranking_eligible: bool
    fairness_note: NonBlank
    caveat: NonBlank
    takeaway: NonBlank
    limitations: list[NonBlank] = Field(min_length=1)
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank
    members: list[ComparisonMember] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_comparison(self) -> ComparisonSet:
        if self.canonical_url != f"/compare/{self.comparison_id}":
            raise ValueError("comparison canonical_url must be generated from comparison_id")
        if self.journey_id != self.case_id:
            raise ValueError("comparison journey_id must equal case_id")
        if (
            self.identity_status == "canonical"
            and self.canonical_comparison_id != self.comparison_id
        ):
            raise ValueError("canonical comparison must identify itself")
        if self.identity_status == "derived" and self.canonical_comparison_id == self.comparison_id:
            raise ValueError("derived comparison must identify its canonical comparison")
        if self.ranking_eligible and self.comparability != "comparable_with_caveat":
            raise ValueError("ranking eligibility requires comparable_with_caveat")
        _require_unique(self.fixed_factors, "fixed_factors")
        _require_unique(self.changed_factors, "changed_factors")
        _require_unique(self.aliases, "aliases")
        _require_unique(self.source_ids, "source_ids")
        _require_unique([metric.metric_id for metric in self.metrics], "metric IDs")
        _require_unique([member.member_id for member in self.members], "member IDs")
        if any(member.budget != self.budget for member in self.members):
            raise ValueError("comparison members must use the declared aligned budget")
        if self.synchronization_axis != self.budget.metric:
            raise ValueError("synchronization_axis must match the aligned budget metric")
        families = {member.artifact.renderer_family for member in self.members}
        if len(families) > 1 and families != {"continuous_trajectory", "generic_metric_history"}:
            raise ValueError("comparison members use incompatible renderer families")
        return self


class ComparisonIndex(ComparisonModel):
    contract_version: Literal["2.0.0"] = "2.0.0"
    dataset_version: NonBlank
    comparisons: list[ComparisonSet] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_index(self) -> ComparisonIndex:
        ids = [comparison.comparison_id for comparison in self.comparisons]
        _require_unique(ids, "comparison IDs")
        canonical_ids = set(ids)
        for comparison in self.comparisons:
            if comparison.canonical_comparison_id not in canonical_ids:
                raise ValueError(
                    "comparison canonical identity does not resolve: "
                    f"{comparison.canonical_comparison_id}"
                )
        return self


def load_comparison_seed(path: Path, dataset_version: str) -> ComparisonIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"comparisons"} or not isinstance(payload["comparisons"], list):
        raise ValueError(f"invalid comparison seed: {path}")
    return ComparisonIndex(dataset_version=dataset_version, comparisons=payload["comparisons"])


def _require_unique(values: list[str], owner: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{owner} must be unique")
