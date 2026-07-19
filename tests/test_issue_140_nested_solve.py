from __future__ import annotations

import json
from pathlib import Path

from optimization_compass.comparisons import (
    ComparisonIndex,
    load_comparison_seed,
    validate_comparison_benchmark_contexts,
)
from optimization_compass.learning_journeys import _case_scenarios
from optimization_compass.nested_solve import (
    BILEVEL_EXACT_SCENARIO_ID,
    BILEVEL_GENERATOR_ID,
    BILEVEL_GENERATOR_VERSION,
    BILEVEL_PROBLEM_DEFINITION_ID,
    BILEVEL_PROBLEM_INSTANCE_ID,
    BILEVEL_RELAXED_SCENARIO_ID,
    HYBRID_CHATTERING_SCENARIO_ID,
    generate_bilevel_regression_traces,
    generate_hybrid_chattering_trace,
)
from optimization_compass.problem_registry import load_problem_suite
from optimization_compass.site_export import _visualization_scenario
from optimization_compass.trace_models import AlgorithmTrace

ROOT = Path(__file__).parents[1]


def _metric_values(trace: AlgorithmTrace, metric_id: str) -> list[float]:
    frames = trace.frames
    return [
        next(metric.value for metric in frame.metrics if metric.metric_id == metric_id)
        for frame in frames
    ]


def test_bilevel_ledgers_separate_outer_inner_and_complementarity() -> None:
    exact, relaxed = generate_bilevel_regression_traces(dataset_version="0.18.9")

    shared_parameters = {
        "outer_step_policy",
        "inner_policy",
        "inner_tolerance",
        "inner_max_iterations",
        "derivative_route",
    }
    assert {key: exact.parameters[key] for key in shared_parameters} == {
        key: relaxed.parameters[key] for key in shared_parameters
    }
    assert exact.evaluation_budget == relaxed.evaluation_budget == 6
    assert exact.parameters["complementarity_treatment"] == "exact_kkt_complementarity"
    assert relaxed.parameters["complementarity_treatment"] == "finite_relaxation"
    assert max(_metric_values(exact, "inner_residual")) <= 1e-8
    assert max(_metric_values(exact, "complementarity_residual")) <= 1e-8
    assert min(_metric_values(relaxed, "complementarity_residual")) >= 4e-3
    assert (
        _metric_values(relaxed, "outer_objective")[-1]
        < _metric_values(exact, "outer_objective")[-1]
    )
    assert relaxed.terminal_status == "stopped"
    assert "exact complementarity is not claimed" in relaxed.terminal_summary_en


def test_nested_scenarios_use_the_existing_metric_history_contract() -> None:
    exact, relaxed = generate_bilevel_regression_traces(dataset_version="0.18.9")
    hybrid = generate_hybrid_chattering_trace(dataset_version="0.18.9")

    scenarios = [_visualization_scenario(trace) for trace in (exact, relaxed, hybrid)]
    by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    assert set(by_id) == {
        BILEVEL_EXACT_SCENARIO_ID,
        BILEVEL_RELAXED_SCENARIO_ID,
        HYBRID_CHATTERING_SCENARIO_ID,
    }
    assert {scenario.artifact.renderer_family for scenario in scenarios} == {
        "generic_metric_history"
    }
    assert by_id[BILEVEL_EXACT_SCENARIO_ID].purpose == "mechanism"
    assert by_id[BILEVEL_RELAXED_SCENARIO_ID].purpose == "failure_contrast"
    assert by_id[HYBRID_CHATTERING_SCENARIO_ID].purpose == "failure_contrast"
    assert "global optimality" in by_id[BILEVEL_EXACT_SCENARIO_ID].lesson.limitations_en
    assert "contact/friction model" in by_id[HYBRID_CHATTERING_SCENARIO_ID].lesson.limitations_en


def test_hybrid_failure_ledger_stops_on_chattering_not_objective_progress() -> None:
    trace = generate_hybrid_chattering_trace(dataset_version="0.18.9")

    assert (
        _metric_values(trace, "objective_value")[-1] < _metric_values(trace, "objective_value")[0]
    )
    assert (
        _metric_values(trace, "dynamics_defect")[-1] < _metric_values(trace, "dynamics_defect")[0]
    )
    assert _metric_values(trace, "mode_switch_count") == list(range(8))
    assert _metric_values(trace, "switching_interval")[-1] < 0.01
    assert trace.terminal_status == "stopped"
    assert trace.preset["contact_model"] == "not_applicable"


def test_bilevel_compare_and_learning_routes_are_linked() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.18.9")
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_BILEVEL_COMPLEMENTARITY_TREATMENT"
    )
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False
    assert comparison.budget.value == 6
    assert comparison.changed_factors == [
        "complementarity treatment only: exact_kkt_complementarity versus "
        "finite_relaxation at tau 1e-2"
    ]
    common = {
        "outer_step_policy",
        "inner_policy",
        "inner_tolerance",
        "inner_max_iterations",
        "derivative_route",
    }
    reference, failure = comparison.members
    assert {key: reference.parameters[key] for key in common} == {
        key: failure.parameters[key] for key in common
    }

    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == comparison.case_id)
    assert set(case["visualization_ids"]) >= {
        BILEVEL_EXACT_SCENARIO_ID,
        BILEVEL_RELAXED_SCENARIO_ID,
    }
    assert case["comparison_ids"] == [comparison.comparison_id]

    article = (ROOT / "content/concepts/nested-equilibrium-complementarity-hybrid.md").read_text(
        encoding="utf-8"
    )
    assert BILEVEL_EXACT_SCENARIO_ID in article
    assert BILEVEL_RELAXED_SCENARIO_ID in article
    assert HYBRID_CHATTERING_SCENARIO_ID in article
    assert comparison.comparison_id in article

    exact, relaxed = generate_bilevel_regression_traces(dataset_version="0.18.9")
    resolved = _case_scenarios(case, [_visualization_scenario(trace) for trace in (exact, relaxed)])
    assert {item.scenario_id for item in resolved} == {
        BILEVEL_EXACT_SCENARIO_ID,
        BILEVEL_RELAXED_SCENARIO_ID,
    }


def test_bilevel_comparison_resolves_canonical_problem_and_exact_context() -> None:
    suite = load_problem_suite()
    assert any(
        item.problem_definition_id == BILEVEL_PROBLEM_DEFINITION_ID for item in suite.definitions
    )
    assert any(item.problem_instance_id == BILEVEL_PROBLEM_INSTANCE_ID for item in suite.instances)

    full_index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.18.9")
    comparison = next(
        item
        for item in full_index.comparisons
        if item.comparison_id == "COMPARE_BILEVEL_COMPLEMENTARITY_TREATMENT"
    )
    index = ComparisonIndex(dataset_version="0.18.9", comparisons=[comparison])
    exact, relaxed = generate_bilevel_regression_traces(dataset_version="0.18.9")
    scenarios = [_visualization_scenario(trace) for trace in (exact, relaxed)]
    generator = {
        "generator_id": BILEVEL_GENERATOR_ID,
        "generator_version": BILEVEL_GENERATOR_VERSION,
        "implementation_mapping_status": "not_applicable",
    }
    context = {
        "context_id": "BENCH_BILEVEL_REGRESSION_EDUCATIONAL_6",
        "problem_instance_id": BILEVEL_PROBLEM_INSTANCE_ID,
        "evaluation_budget": 6,
        "oracle_budget": {"unit": "oracle_evaluations", "limit": 6},
        "runtime": {"comparison_scope": "exact", **generator},
        "implementation_versions": generator,
        "stopping": {"policy": "fixed_outer_budget", "value": 6},
        "initialization": {"policy": "fixed_outer_initialization", "points": [0.8]},
        "seed_status": "not_applicable",
        "seed_value": None,
    }

    validate_comparison_benchmark_contexts(index, [context], scenarios)
