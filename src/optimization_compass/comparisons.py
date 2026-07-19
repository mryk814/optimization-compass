from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from optimization_compass.nested_solve import (
    BILEVEL_GENERATOR_ID,
    BILEVEL_GENERATOR_VERSION,
    BILEVEL_PROFILE_ID,
    HYBRID_GENERATOR_ID,
    HYBRID_GENERATOR_VERSION,
    HYBRID_PROFILE_ID,
)
from optimization_compass.portfolio_uncertainty import (
    GENERATOR_ID as PORTFOLIO_GENERATOR_ID,
)
from optimization_compass.portfolio_uncertainty import (
    GENERATOR_VERSION as PORTFOLIO_GENERATOR_VERSION,
)
from optimization_compass.portfolio_uncertainty import (
    PROFILE_ID as PORTFOLIO_PROFILE_ID,
)
from optimization_compass.search_tree import (
    SEARCH_TREE_GENERATOR_ID,
    SEARCH_TREE_GENERATOR_VERSION,
    SEARCH_TREE_HEURISTIC_INCUMBENT_ASSIGNMENT,
    SEARCH_TREE_HEURISTIC_INCUMBENT_VALUE,
)
from optimization_compass.surrogate_uncertainty import (
    SURROGATE_GENERATOR_ID,
    SURROGATE_GENERATOR_VERSION,
)
from optimization_compass.trace_models import AlgorithmTrace
from optimization_compass.visualization_scenarios import VisualizationScenario

_EDUCATIONAL_GENERATORS_BY_RENDERER = {
    "search_tree": (SEARCH_TREE_GENERATOR_ID, SEARCH_TREE_GENERATOR_VERSION),
    "surrogate_uncertainty": (SURROGATE_GENERATOR_ID, SURROGATE_GENERATOR_VERSION),
    "simplex_geometry": ("educational.nelder_mead.v1", "1.0.0"),
    "field_evolution": ("educational.topology_optimization.v1", "1.0.0"),
    "generic_metric_history": ("educational.optimal_control.v1", "1.1.0"),
}
_EDUCATIONAL_GENERATORS_BY_PROFILE = {
    BILEVEL_PROFILE_ID: (BILEVEL_GENERATOR_ID, BILEVEL_GENERATOR_VERSION),
    HYBRID_PROFILE_ID: (HYBRID_GENERATOR_ID, HYBRID_GENERATOR_VERSION),
    PORTFOLIO_PROFILE_ID: (PORTFOLIO_GENERATOR_ID, PORTFOLIO_GENERATOR_VERSION),
}
_EDUCATIONAL_INITIALIZATION_BY_RENDERER: dict[str, dict[str, object]] = {
    "search_tree": {
        "policy": "fixed_empty_assignment_with_heuristic_incumbent",
        "heuristic_incumbent_assignment": SEARCH_TREE_HEURISTIC_INCUMBENT_ASSIGNMENT,
        "heuristic_incumbent_value": SEARCH_TREE_HEURISTIC_INCUMBENT_VALUE,
    },
    "field_evolution": {"policy": "fixed_density_field", "points": [0.5] * 32},
}

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
    "simplex_geometry",
    "feasible_region",
    "pareto_front",
    "field_evolution",
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
                "simplex_geometry",
                "feasible_region",
                "field_evolution",
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


def validate_comparison_benchmark_contexts(
    index: ComparisonIndex,
    contexts: Iterable[Mapping[str, Any]],
    scenarios: Iterable[VisualizationScenario],
    *,
    problem_definition_ids: Iterable[str] | None = None,
    problem_instance_ids: Iterable[str] | None = None,
    traces: Iterable[AlgorithmTrace] = (),
) -> None:
    contexts_by_id = {str(context["context_id"]): context for context in contexts}
    scenarios_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    known_problem_definitions = (
        set(problem_definition_ids) if problem_definition_ids is not None else None
    )
    known_problem_instances = (
        set(problem_instance_ids) if problem_instance_ids is not None else None
    )
    traces_by_id = {trace.trace_id: trace for trace in traces}
    exact_context_ids = {
        context_id
        for context_id, context in contexts_by_id.items()
        if isinstance(context.get("runtime"), Mapping)
        and context["runtime"].get("comparison_scope") == "exact"
    }
    referenced_exact_context_ids: set[str] = set()
    for comparison in index.comparisons:
        if (
            known_problem_definitions is not None
            and comparison.problem_definition_id not in known_problem_definitions
        ):
            raise ValueError(
                "comparison problem definition does not resolve: "
                f"{comparison.problem_definition_id}"
            )
        if (
            known_problem_instances is not None
            and comparison.problem_instance_id not in known_problem_instances
        ):
            raise ValueError(
                f"comparison problem instance does not resolve: {comparison.problem_instance_id}"
            )
        context = contexts_by_id.get(comparison.benchmark_context_id)
        if context is None:
            raise ValueError(
                f"comparison benchmark context does not resolve: {comparison.benchmark_context_id}"
            )
        if comparison.benchmark_context_id not in exact_context_ids:
            continue
        if context.get("problem_instance_id") != comparison.problem_instance_id:
            raise ValueError(
                "exact comparison benchmark context uses a different problem instance: "
                f"{comparison.comparison_id} expects {comparison.problem_instance_id}, "
                f"{comparison.benchmark_context_id} uses {context.get('problem_instance_id')}"
            )
        referenced_exact_context_ids.add(comparison.benchmark_context_id)
        _validate_exact_comparison_context(
            comparison,
            context,
            scenarios_by_id,
            traces_by_id,
        )
    unreferenced = exact_context_ids - referenced_exact_context_ids
    if unreferenced:
        raise ValueError(f"exact benchmark context is not referenced: {sorted(unreferenced)}")


def _validate_exact_comparison_context(
    comparison: ComparisonSet,
    context: Mapping[str, Any],
    scenarios_by_id: Mapping[str, VisualizationScenario],
    traces_by_id: Mapping[str, AlgorithmTrace],
) -> None:
    runtime = context["runtime"]
    implementation = context["implementation_versions"]
    initialization = context["initialization"]
    oracle_budget = context["oracle_budget"]
    stopping = context["stopping"]
    if not all(
        isinstance(item, Mapping)
        for item in (runtime, implementation, initialization, oracle_budget, stopping)
    ):
        raise ValueError(f"exact benchmark context is malformed: {context['context_id']}")
    expected = {
        "problem_instance_id": comparison.problem_instance_id,
        "evaluation_budget": comparison.budget.value,
        "oracle_budget_limit": comparison.budget.value,
        "oracle_budget_unit": comparison.budget.metric,
    }
    observed = {
        "problem_instance_id": context["problem_instance_id"],
        "evaluation_budget": context["evaluation_budget"],
        "oracle_budget_limit": oracle_budget.get("limit"),
        "oracle_budget_unit": oracle_budget.get("unit"),
    }
    if observed != expected:
        raise ValueError(
            f"comparison benchmark context differs from {comparison.comparison_id}: "
            f"expected {expected}, observed {observed}"
        )
    if implementation.get("implementation_mapping_status") != "not_applicable":
        raise ValueError("educational comparison context must mark implementation not_applicable")
    if runtime.get("generator_id") != implementation.get("generator_id") or runtime.get(
        "generator_version"
    ) != implementation.get("generator_version"):
        raise ValueError("educational comparison generator identity is inconsistent")
    expected_generators: set[tuple[str, str]] = set()
    renderer_families: set[str] = set()
    for member in comparison.members:
        scenario = scenarios_by_id.get(member.scenario_id)
        if scenario is None:
            raise ValueError(f"comparison scenario does not resolve: {member.scenario_id}")
        run = next(
            (
                candidate
                for candidate in scenario.runs
                if candidate.artifact_id == member.artifact.artifact_id
                and candidate.method_id == member.method_id
            ),
            None,
        )
        trace = traces_by_id.get(member.artifact.artifact_id)
        expected_generator = (
            (trace.generator_id, trace.generator_version)
            if trace is not None
            else _EDUCATIONAL_GENERATORS_BY_PROFILE.get(run.profile_id)
            if run is not None
            else None
        ) or _EDUCATIONAL_GENERATORS_BY_RENDERER.get(scenario.artifact.renderer_family)
        if run is None:
            raise ValueError(f"comparison member run does not resolve: {member.member_id}")
        if expected_generator is None:
            raise ValueError(
                "educational comparison renderer has no registered generator: "
                f"{scenario.artifact.renderer_family}"
            )
        expected_generators.add(expected_generator)
        renderer_families.add(scenario.artifact.renderer_family)
    if len(expected_generators) != 1 or (
        runtime.get("generator_id"),
        runtime.get("generator_version"),
    ) != next(iter(expected_generators)):
        raise ValueError("educational comparison context uses an unknown generator")
    if context.get("seed_status") == "fixed" and context.get("seed_value") is None:
        raise ValueError("fixed educational comparison context requires a seed value")
    if context.get("seed_status") == "not_applicable" and context.get("seed_value") is not None:
        raise ValueError(
            "seed-not-applicable educational comparison context must omit a seed value"
        )
    if context.get("seed_status") not in {"fixed", "not_applicable"}:
        raise ValueError("exact educational comparison context has an unsupported seed status")
    if len(renderer_families) != 1:
        raise ValueError("exact educational comparison must use one renderer family")
    expected_initialization = _EDUCATIONAL_INITIALIZATION_BY_RENDERER.get(
        next(iter(renderer_families))
    )
    if expected_initialization is not None and any(
        initialization.get(key) != value for key, value in expected_initialization.items()
    ):
        raise ValueError("exact benchmark initialization differs from canonical generator")
    initial_points = initialization.get("points")
    member_initial_points = initialization.get("policy") == "member_initial_points"
    if member_initial_points and not isinstance(initial_points, list):
        raise ValueError("member-initial-point comparison context requires points")
    member_parameter = runtime.get("member_parameter")
    expected_member_values = stopping.get("member_values")
    observed_member_values: list[object] = []
    if member_parameter is not None and (
        not isinstance(member_parameter, str)
        or not isinstance(expected_member_values, list)
        or not expected_member_values
    ):
        raise ValueError("exact benchmark member parameter policy is malformed")
    for member in comparison.members:
        scenario = scenarios_by_id.get(member.scenario_id)
        if scenario is None:
            raise ValueError(f"comparison scenario does not resolve: {member.scenario_id}")
        run = next(
            (
                candidate
                for candidate in scenario.runs
                if candidate.artifact_id == member.artifact.artifact_id
                and candidate.method_id == member.method_id
            ),
            None,
        )
        if run is None:
            raise ValueError(f"comparison member run does not resolve: {member.member_id}")
        if (
            scenario.problem_instance_id != context["problem_instance_id"]
            or scenario.experiment.budget.metric != comparison.budget.metric
            or scenario.experiment.budget.value != context["evaluation_budget"]
            or scenario.experiment.seed.status != context["seed_status"]
            or scenario.experiment.seed.value != context["seed_value"]
            or (
                not member_initial_points
                and scenario.experiment.initial_condition.point != initial_points
            )
            or run.implementation_mapping_status != implementation["implementation_mapping_status"]
        ):
            raise ValueError(f"comparison member differs from exact context: {member.member_id}")
        if isinstance(member_parameter, str):
            member_value = member.parameters.get(member_parameter)
            observed_member_values.append(member_value)
            if member_value != scenario.experiment.stopping.get("max_nodes"):
                raise ValueError(
                    f"comparison member stop limit differs from scenario: {member.member_id}"
                )
    if member_initial_points:
        observed_initial_points = [
            scenario.experiment.initial_condition.point
            for member in comparison.members
            if (scenario := scenarios_by_id.get(member.scenario_id)) is not None
        ]
        if sorted(
            json.dumps(point, ensure_ascii=False, separators=(",", ":"))
            for point in observed_initial_points
        ) != sorted(
            json.dumps(point, ensure_ascii=False, separators=(",", ":")) for point in initial_points
        ):
            raise ValueError("comparison member initial points differ from exact context")
    if isinstance(member_parameter, str) and sorted(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for value in observed_member_values
    ) != sorted(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for value in expected_member_values
    ):
        raise ValueError("comparison member values differ from exact context")


def _require_unique(values: list[str], owner: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{owner} must be unique")
