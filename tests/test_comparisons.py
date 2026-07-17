import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.comparisons import (
    ComparisonIndex,
    ComparisonMember,
    load_comparison_seed,
    validate_comparison_benchmark_contexts,
)
from optimization_compass.search_tree import (
    SEARCH_TREE_GENERATOR_ID,
    SEARCH_TREE_GENERATOR_VERSION,
    SEARCH_TREE_HEURISTIC_INCUMBENT_ASSIGNMENT,
    SEARCH_TREE_HEURISTIC_INCUMBENT_VALUE,
    generate_search_tree_artifact,
)
from optimization_compass.site_export import _visualization_scenario
from optimization_compass.surrogate_uncertainty import (
    SURROGATE_GENERATOR_ID,
    SURROGATE_GENERATOR_VERSION,
    generate_surrogate_scenario,
)

ROOT = Path(__file__).parents[1]


def test_seed_expresses_multiple_modes_and_renderer_families() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.13.0")

    assert {comparison.mode for comparison in index.comparisons} >= {
        "method_contrast",
        "parameter_sensitivity",
        "failure_contrast",
        "result_tradeoff",
        "strategy_contrast",
    }
    assert {
        member.artifact.renderer_family
        for comparison in index.comparisons
        for member in comparison.members
    } >= {
        "continuous_trajectory",
        "feasible_region",
        "pareto_front",
        "surrogate_uncertainty",
    }


def test_bo_comparison_is_a_non_ranking_one_factor_contrast() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.13.0")
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_BO_ACQUISITION_NOISE_BASELINE"
    )

    assert comparison.problem_instance_id == "OBJECTIVE_EDUCATIONAL_WAVY_1D"
    assert comparison.benchmark_context_id == "BENCH_BO_EDUCATIONAL_10"
    assert comparison.budget.metric == comparison.synchronization_axis == "oracle_evaluations"
    assert comparison.budget.value == 10
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False
    assert {member.role for member in comparison.members} == {
        "reference_acquisition",
        "acquisition_sensitivity",
        "noise_sensitivity",
        "random_baseline",
    }
    assert {member.artifact.renderer_family for member in comparison.members} == {
        "surrogate_uncertainty"
    }
    members = {member.role: member for member in comparison.members}
    reference_factors = _semantic_factors(members["reference_acquisition"])
    assert _changed_factors(
        reference_factors, _semantic_factors(members["acquisition_sensitivity"])
    ) == {"proposal"}
    assert _changed_factors(reference_factors, _semantic_factors(members["noise_sensitivity"])) == {
        "noise_std"
    }
    assert _changed_factors(reference_factors, _semantic_factors(members["random_baseline"])) == {
        "proposal"
    }
    assert members["random_baseline"].parameters["exploration_xi"] == "not_applicable"


def test_bo_comparison_matches_its_exact_educational_context() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.13.0")
    bo_index = ComparisonIndex(
        dataset_version=index.dataset_version,
        comparisons=[
            comparison
            for comparison in index.comparisons
            if comparison.comparison_id == "COMPARE_BO_ACQUISITION_NOISE_BASELINE"
        ],
    )
    scenarios = [
        generate_surrogate_scenario(
            dataset_version="0.13.0",
            strategy=strategy,
            noise_preset=noise,
        ).scenario
        for strategy in ("exploit", "explore")
        for noise in ("noiseless", "small_noise")
    ]
    context = _bo_context()

    validate_comparison_benchmark_contexts(bo_index, [context], scenarios)
    context["evaluation_budget"] = 25
    with pytest.raises(ValueError, match="benchmark context differs"):
        validate_comparison_benchmark_contexts(bo_index, [context], scenarios)


def test_hpo_method_reasons_have_direct_canonical_sources() -> None:
    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "hyperparameter-search")

    assert {"S002", "S056"} <= set(case["source_ids"])


def test_budget_allocation_case_matches_the_canonical_knapsack_lesson() -> None:
    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "budget-allocation")

    assert case["problem_archetype_id"] == "PA032"
    assert set(case["question_answers"]) == {f"Q{index:02d}" for index in range(1, 13)}
    assert {"S002", "S021", "S022", "S079"} <= set(case["source_ids"])
    assert set(case["visualization_ids"]) >= {
        "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE",
        "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET",
    }
    assert case["comparison_ids"] == ["COMPARE_KNAPSACK_BNB_BUDGET"]
    compile(case["python_example"], "<budget-allocation>", "exec")


def test_knapsack_comparison_is_a_non_ranking_one_factor_stop_contrast() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.14.0")
    comparison = next(
        item for item in index.comparisons if item.comparison_id == "COMPARE_KNAPSACK_BNB_BUDGET"
    )

    assert comparison.problem_definition_id == "PROBLEM_BINARY_KNAPSACK"
    assert comparison.problem_instance_id == "INSTANCE_BINARY_KNAPSACK_4"
    assert comparison.benchmark_context_id == "BENCH_KNAPSACK_BNB_EDUCATIONAL_9"
    assert comparison.mode == "failure_contrast"
    assert comparison.budget.metric == comparison.synchronization_axis == "oracle_evaluations"
    assert comparison.budget.value == 9
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False
    assert {member.parameters["node_stop_limit"] for member in comparison.members} == {4, 9}
    assert all(set(member.parameters) == {"node_stop_limit"} for member in comparison.members)
    assert {member.artifact.payload_path for member in comparison.members} == {
        "search-trees/binary-knapsack-bnb-complete.json",
        "search-trees/binary-knapsack-bnb-budget.json",
    }


def test_knapsack_comparison_matches_its_exact_educational_context() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.14.0")
    knapsack_index = ComparisonIndex(
        dataset_version=index.dataset_version,
        comparisons=[
            comparison
            for comparison in index.comparisons
            if comparison.comparison_id == "COMPARE_KNAPSACK_BNB_BUDGET"
        ],
    )
    scenarios = [
        _visualization_scenario(
            generate_search_tree_artifact(
                dataset_version="0.14.0", node_stop_limit=node_stop_limit
            ).trace
        )
        for node_stop_limit in (9, 4)
    ]
    context = _knapsack_context()

    validate_comparison_benchmark_contexts(knapsack_index, [context], scenarios)
    context["initialization"]["heuristic_incumbent_value"] = 12
    with pytest.raises(ValueError, match="initialization differs"):
        validate_comparison_benchmark_contexts(knapsack_index, [context], scenarios)
    context = _knapsack_context()
    context["initialization"]["heuristic_incumbent_assignment"] = {"A": 1}
    with pytest.raises(ValueError, match="initialization differs"):
        validate_comparison_benchmark_contexts(knapsack_index, [context], scenarios)
    context = _knapsack_context()
    context["stopping"] = {"policy": "member_node_stop_limit", "member_values": [3, 9]}
    with pytest.raises(ValueError, match="member values differ"):
        validate_comparison_benchmark_contexts(knapsack_index, [context], scenarios)


def test_pareto_comparison_uses_three_weighted_sum_preference_members() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.15.0")
    comparison = next(
        item for item in index.comparisons if item.comparison_id == "COMPARE_PARETO_PREFERENCE"
    )

    assert comparison.problem_instance_id == "INSTANCE_BIOBJECTIVE_QUADRATIC_2D"
    assert comparison.mode == "result_tradeoff"
    assert comparison.comparability == "not_comparable"
    assert comparison.ranking_eligible is False
    assert [member.parameters["weight_f1"] for member in comparison.members] == [0.2, 0.5, 0.8]
    assert {member.method_id for member in comparison.members} == {"M_WEIGHTED_SUM"}
    assert {member.scenario_id for member in comparison.members} == {
        "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY"
    }
    assert {member.artifact.artifact_id for member in comparison.members} == {
        "biobjective-quadratic-pareto-front"
    }


def test_ec017_formulation_distinguishes_the_real_case_from_the_fixed_lesson() -> None:
    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "EC017")

    assert "f₁=x²+y²" in case["objective"]
    assert "f₂=(x−2)²+(y−2)²" in case["objective"]
    assert any("同一視しません" in limitation for limitation in case["limitations"])


def test_rejects_unfair_budget_alignment() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.13.0")
    payload = index.model_dump(mode="json")
    payload["comparisons"][0]["members"][0]["budget"]["value"] += 1

    with pytest.raises(ValidationError, match="aligned budget"):
        ComparisonIndex.model_validate(payload)


def test_rejects_incompatible_artifact_kind() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.13.0")
    payload = deepcopy(index.model_dump(mode="json"))
    constrained = next(
        comparison
        for comparison in payload["comparisons"]
        if comparison["mode"] == "failure_contrast"
    )
    constrained["members"][0]["artifact"]["artifact_kind"] = "result_visualization"

    with pytest.raises(ValidationError, match="feasible_region requires an executable_trace"):
        ComparisonIndex.model_validate(payload)


def _semantic_factors(member: ComparisonMember) -> dict[str, object]:
    policy = member.parameters["proposal_policy"]
    proposal = (
        (policy, member.parameters["exploration_xi"])
        if policy == "expected_improvement"
        else (policy,)
    )
    return {"proposal": proposal, "noise_std": member.parameters["noise_std"]}


def _changed_factors(reference: dict[str, object], candidate: dict[str, object]) -> set[str]:
    return {key for key in reference if reference[key] != candidate[key]}


def _bo_context() -> dict[str, object]:
    generator = {
        "implementation_mapping_status": "not_applicable",
        "generator_id": SURROGATE_GENERATOR_ID,
        "generator_version": SURROGATE_GENERATOR_VERSION,
    }
    return {
        "context_id": "BENCH_BO_EDUCATIONAL_10",
        "problem_instance_id": "OBJECTIVE_EDUCATIONAL_WAVY_1D",
        "evaluation_budget": 10,
        "oracle_budget": {"unit": "oracle_evaluations", "limit": 10},
        "runtime": {
            "comparison_scope": "exact",
            "generator_id": SURROGATE_GENERATOR_ID,
            "generator_version": SURROGATE_GENERATOR_VERSION,
        },
        "implementation_versions": generator,
        "stopping": {"policy": "fixed_oracle_budget", "value": 10},
        "initialization": {"policy": "fixed_initial_design", "points": [-2.6, 0.0, 2.6]},
        "seed_status": "fixed",
        "seed_value": 2604,
    }


def _knapsack_context() -> dict[str, object]:
    generator = {
        "implementation_mapping_status": "not_applicable",
        "generator_id": SEARCH_TREE_GENERATOR_ID,
        "generator_version": SEARCH_TREE_GENERATOR_VERSION,
    }
    return {
        "context_id": "BENCH_KNAPSACK_BNB_EDUCATIONAL_9",
        "problem_instance_id": "INSTANCE_BINARY_KNAPSACK_4",
        "evaluation_budget": 9,
        "oracle_budget": {"unit": "oracle_evaluations", "limit": 9},
        "runtime": {
            "comparison_scope": "exact",
            "generator_id": SEARCH_TREE_GENERATOR_ID,
            "generator_version": SEARCH_TREE_GENERATOR_VERSION,
            "member_parameter": "node_stop_limit",
        },
        "implementation_versions": generator,
        "stopping": {"policy": "member_node_stop_limit", "member_values": [4, 9]},
        "initialization": {
            "policy": "fixed_empty_assignment_with_heuristic_incumbent",
            "points": [0.0, 0.0, 0.0, 0.0],
            "heuristic_incumbent_assignment": SEARCH_TREE_HEURISTIC_INCUMBENT_ASSIGNMENT,
            "heuristic_incumbent_value": SEARCH_TREE_HEURISTIC_INCUMBENT_VALUE,
        },
        "seed_status": "fixed",
        "seed_value": 0,
    }
