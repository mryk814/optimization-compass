from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.comparisons import (
    load_comparison_seed,
    validate_comparison_benchmark_contexts,
)
from optimization_compass.simulation_constrained import (
    FAILURE_SCENARIO_ID,
    LOOSE_SCENARIO_ID,
    TIGHT_SCENARIO_ID,
    generate_simulation_constrained_traces,
)
from optimization_compass.site_export import _visualization_scenario
from optimization_compass.visualization_scenarios import scenario_identity

ROOT = Path(__file__).parents[1]


def test_simulation_constrained_journey_separates_cost_residual_and_failure() -> None:
    traces = generate_simulation_constrained_traces(dataset_version="0.18.7")
    by_scenario = {trace.scenario_id: trace for trace in traces}

    assert set(by_scenario) == {
        TIGHT_SCENARIO_ID,
        LOOSE_SCENARIO_ID,
        FAILURE_SCENARIO_ID,
    }
    tight = by_scenario[TIGHT_SCENARIO_ID]
    loose = by_scenario[LOOSE_SCENARIO_ID]
    assert tight.parameters["state_tolerance"] == 1e-8
    assert loose.parameters["state_tolerance"] == 1e-3
    assert (
        tight.frames[-1].payload["state_linear_iterations"]
        > loose.frames[-1].payload["state_linear_iterations"]
    )
    assert tight.frames[-1].payload["state_residual"] < loose.frames[-1].payload["state_residual"]

    failure = by_scenario[FAILURE_SCENARIO_ID]
    final = failure.frames[-1]
    assert failure.terminal_status == "failed"
    assert final.payload["evaluation_status"] == "diverged_pc_failed"
    assert final.payload["objective_value"] is None
    assert final.payload["failure_is_penalty_value"] is False
    assert all(metric.metric_id != "objective_value" for metric in final.metrics)


def test_simulation_scenarios_keep_canonical_identity_and_problem_authority() -> None:
    scenarios = [
        _visualization_scenario(trace)
        for trace in generate_simulation_constrained_traces(dataset_version="0.18.7")
    ]
    by_id = {scenario.scenario_id: scenario for scenario in scenarios}

    assert scenario_identity(TIGHT_SCENARIO_ID) == ("canonical", TIGHT_SCENARIO_ID)
    assert scenario_identity(LOOSE_SCENARIO_ID) == ("derived", TIGHT_SCENARIO_ID)
    assert scenario_identity(FAILURE_SCENARIO_ID) == ("derived", TIGHT_SCENARIO_ID)
    assert all(
        scenario.problem_instance_id == "INSTANCE_TOPOLOGY_CANTILEVER_2D" for scenario in scenarios
    )
    assert by_id[FAILURE_SCENARIO_ID].purpose == "failure_contrast"
    assert by_id[LOOSE_SCENARIO_ID].purpose == "sensitivity"
    assert all(
        scenario.artifact.renderer_family == "generic_metric_history" for scenario in scenarios
    )


def test_ec026_links_primary_failure_and_tolerance_compare() -> None:
    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "EC026")

    assert {TIGHT_SCENARIO_ID, LOOSE_SCENARIO_ID, FAILURE_SCENARIO_ID} <= set(
        case["visualization_ids"]
    )
    assert case["comparison_ids"] == ["COMPARE_PDE_STATE_TOLERANCE_COST"]
    assert "failed evaluation" in case["practical_notes"]
    assert "checkpoint" in case["practical_notes"]
    assert "coupling iteration" in case["practical_notes"]


def test_pde_tolerance_compare_fixes_every_factor_except_inner_tolerance() -> None:
    index = load_comparison_seed(
        ROOT / "data/seeds/site_comparisons.json", dataset_version="0.18.7"
    )
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_PDE_STATE_TOLERANCE_COST"
    )

    assert comparison.problem_instance_id == "INSTANCE_TOPOLOGY_CANTILEVER_2D"
    assert comparison.benchmark_context_id == "BENCH_PDE_STATE_TOLERANCE_6"
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False
    assert comparison.budget.metric == comparison.synchronization_axis == "oracle_evaluations"
    assert comparison.changed_factors == ["state/adjoint relative toleranceだけ: 1e-8 対 1e-3"]
    assert {member.scenario_id for member in comparison.members} == {
        TIGHT_SCENARIO_ID,
        LOOSE_SCENARIO_ID,
    }
    assert all(member.budget == comparison.budget for member in comparison.members)


def test_exact_benchmark_contexts_must_match_the_comparison_problem_instance() -> None:
    index = load_comparison_seed(
        ROOT / "data/seeds/site_comparisons.json", dataset_version="0.18.7"
    )
    comparison = next(
        item for item in index.comparisons if item.comparison_id == "COMPARE_GRADIENT_FAMILY"
    )
    one_item_index = index.model_copy(update={"comparisons": [comparison]})
    context = {
        "context_id": comparison.benchmark_context_id,
        "problem_instance_id": "WRONG_INSTANCE",
        "runtime": {"comparison_scope": "exact"},
    }

    with pytest.raises(ValueError, match="different problem instance"):
        validate_comparison_benchmark_contexts(one_item_index, [context], [])


def test_pde_article_documents_cost_failure_transient_and_coupling_contracts() -> None:
    article = (ROOT / "content/concepts/pde-constrained-optimization.md").read_text(
        encoding="utf-8"
    )

    for required in (
        "costはoptimizer iterationで数えない",
        "failed evaluationを目的値へ隠さない",
        "transientとmultiphysicsでは追加の軸を持つ",
        "checkpoint policy",
        "coupling residual",
        "COMPARE_PDE_STATE_TOLERANCE_COST",
    ):
        assert required in article
