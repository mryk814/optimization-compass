from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.comparisons import ComparisonIndex, load_comparison_seed

ROOT = Path(__file__).parents[1]


def test_seed_expresses_multiple_modes_and_renderer_families() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.12.0")

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
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.12.0")
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_BO_ACQUISITION_NOISE_BASELINE"
    )

    assert comparison.problem_instance_id == "OBJECTIVE_EDUCATIONAL_WAVY_1D"
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


def test_rejects_unfair_budget_alignment() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.12.0")
    payload = index.model_dump(mode="json")
    payload["comparisons"][0]["members"][0]["budget"]["value"] += 1

    with pytest.raises(ValidationError, match="aligned budget"):
        ComparisonIndex.model_validate(payload)


def test_rejects_incompatible_artifact_kind() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.12.0")
    payload = deepcopy(index.model_dump(mode="json"))
    constrained = next(
        comparison
        for comparison in payload["comparisons"]
        if comparison["mode"] == "failure_contrast"
    )
    constrained["members"][0]["artifact"]["artifact_kind"] = "result_visualization"

    with pytest.raises(ValidationError, match="feasible_region requires an executable_trace"):
        ComparisonIndex.model_validate(payload)
