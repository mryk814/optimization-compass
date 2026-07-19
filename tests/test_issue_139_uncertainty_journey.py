from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.comparisons import load_comparison_seed
from optimization_compass.dataset_release import build_staged_release
from optimization_compass.portfolio_uncertainty import (
    CVAR_SCENARIO_ID,
    CVAR_TRACE_ID,
    NOMINAL_SCENARIO_ID,
    NOMINAL_TRACE_ID,
    PROBLEM_DEFINITION_ID,
    PROBLEM_INSTANCE_ID,
    build_portfolio_uncertainty_scenario,
    generate_portfolio_uncertainty_traces,
)
from optimization_compass.trace_models import AlgorithmTrace
from optimization_compass.visualization_scenarios import VisualizationScenarioIndex

BASE_DATABASE = Path("data/optimization_method_selection_database_v0.2.0.sqlite")


def test_fixed_portfolio_traces_separate_training_and_held_out_risk() -> None:
    nominal, cvar = generate_portfolio_uncertainty_traces(dataset_version="test")

    assert nominal.trace_id == NOMINAL_TRACE_ID
    assert cvar.trace_id == CVAR_TRACE_ID
    assert nominal.initial_state["point"] == [0.45, 0.0, 0.0, 0.55]
    assert cvar.initial_state["point"] == [0.3, 0.4, 0.0, 0.3]
    assert [frame.oracle_evaluations for frame in nominal.frames] == [0, 8, 12]
    assert [frame.payload["split"] for frame in nominal.frames] == [
        "initial",
        "training",
        "held_out",
    ]
    assert [frame.payload["sample_count"] for frame in nominal.frames] == [0, 8, 4]
    assert nominal.parameters["sample_policy"] == cvar.parameters["sample_policy"]
    assert nominal.parameters["risk_level"] == cvar.parameters["risk_level"] == 0.75
    assert nominal.parameters["confidence_target"] == cvar.parameters["confidence_target"]
    assert nominal.parameters["confidence_target"] == "not_applicable_no_probability_guarantee"

    nominal_train = {metric.metric_id: metric.value for metric in nominal.frames[1].metrics}
    nominal_held = {metric.metric_id: metric.value for metric in nominal.frames[2].metrics}
    cvar_train = {metric.metric_id: metric.value for metric in cvar.frames[1].metrics}
    cvar_held = {metric.metric_id: metric.value for metric in cvar.frames[2].metrics}
    assert nominal_train == {
        "mean_loss": pytest.approx(-0.00875),
        "cvar_75": pytest.approx(0.01775),
        "worst_loss": pytest.approx(0.0215),
        "best_loss": pytest.approx(-0.058),
    }
    assert cvar_train["mean_loss"] == pytest.approx(nominal_train["mean_loss"])
    assert cvar_train["cvar_75"] == pytest.approx(0.0065)
    assert nominal_held["cvar_75"] == pytest.approx(0.018)
    assert cvar_held["cvar_75"] == pytest.approx(0.007)


def test_portfolio_scenarios_reuse_algorithm_trace_metric_history_contract() -> None:
    traces = generate_portfolio_uncertainty_traces(dataset_version="test")
    scenarios = [build_portfolio_uncertainty_scenario(trace) for trace in traces]

    assert {scenario.scenario_id for scenario in scenarios} == {
        NOMINAL_SCENARIO_ID,
        CVAR_SCENARIO_ID,
    }
    assert {scenario.identity_status for scenario in scenarios} == {"generated_only"}
    assert {scenario.artifact.renderer_family for scenario in scenarios} == {
        "generic_metric_history"
    }
    assert {scenario.artifact.artifact_contract for scenario in scenarios} == {"AlgorithmTrace"}
    assert {scenario.purpose for scenario in scenarios} == {"mechanism", "sensitivity"}
    nominal = next(
        scenario for scenario in scenarios if scenario.scenario_id == NOMINAL_SCENARIO_ID
    )
    assert nominal.lesson.failure_signals
    assert all("population-risk" in scenario.lesson.limitations_en for scenario in scenarios)


def test_portfolio_compare_changes_only_training_risk_treatment() -> None:
    index = load_comparison_seed(Path("data/seeds/site_comparisons.json"), "test")
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4"
    )

    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False
    assert comparison.budget.metric == comparison.synchronization_axis == "oracle_evaluations"
    assert comparison.budget.value == 12
    assert comparison.problem_definition_id == PROBLEM_DEFINITION_ID
    assert comparison.problem_instance_id == PROBLEM_INSTANCE_ID
    assert comparison.benchmark_context_id == "BENCH_PORTFOLIO_CVAR_FIXED_8_4"
    assert len(comparison.changed_factors) == 1
    assert "risk treatmentだけ" in comparison.changed_factors[0]
    nominal, cvar = comparison.members
    shared_parameter_keys = {
        "uncertainty_model",
        "sample_policy",
        "risk_level",
        "confidence_target",
        "grid_step",
    }
    assert {key: nominal.parameters[key] for key in shared_parameter_keys} == {
        key: cvar.parameters[key] for key in shared_parameter_keys
    }
    assert nominal.parameters["risk_treatment"] != cvar.parameters["risk_treatment"]
    assert nominal.parameters["risk_weight"] != cvar.parameters["risk_weight"]


def test_portfolio_case_connects_theater_compare_and_simplex_guidance() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "portfolio-cvar-allocation")

    assert case["visualization_ids"] == [
        "VIEW_PROBLEM_STRUCTURE",
        NOMINAL_SCENARIO_ID,
        CVAR_SCENARIO_ID,
    ]
    assert case["comparison_ids"] == ["COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4"]
    assert "concept.simplex" in case["practical_notes"]
    assert "sample size" in case["limitations"][2]
    assert "held-out" in case["limitations"][2]


def test_uncertainty_method_source_audit_records_release_boundary_and_primary_backlog() -> None:
    audit = Path("docs/research/uncertainty-method-source-audit.md").read_text(encoding="utf-8")

    for required in (
        "robust optimization",
        "sample-average approximation",
        "chance-constrained optimization",
        "distributionally robust optimization",
        "Rockafellar and Uryasev",
        "Campi and Garatti",
        "Mohajerin Esfahani and Kuhn",
        "versioned dataset migration",
        "confidence target is explicitly `not_applicable`",
        "closed capped simplex",
    ):
        assert required in audit


def test_staged_site_export_contains_portfolio_traces_scenarios_and_comparison(
    tmp_path: Path,
) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    output = release.site_data_directory

    nominal = AlgorithmTrace.model_validate_json(
        (output / "traces" / f"{NOMINAL_TRACE_ID}.json").read_bytes()
    )
    cvar = AlgorithmTrace.model_validate_json(
        (output / "traces" / f"{CVAR_TRACE_ID}.json").read_bytes()
    )
    scenarios = VisualizationScenarioIndex.model_validate_json(
        (output / "visualization-scenarios.json").read_bytes()
    )
    comparisons = json.loads((output / "comparisons.json").read_text(encoding="utf-8"))
    journeys = json.loads((output / "learning-journeys.json").read_text(encoding="utf-8"))

    assert nominal.scenario_id == NOMINAL_SCENARIO_ID
    assert cvar.scenario_id == CVAR_SCENARIO_ID
    assert {NOMINAL_SCENARIO_ID, CVAR_SCENARIO_ID}.issubset(
        {scenario.scenario_id for scenario in scenarios.scenarios}
    )
    assert "COMPARE_PORTFOLIO_NOMINAL_CVAR_8_4" in {
        comparison["comparison_id"] for comparison in comparisons["comparisons"]
    }
    journey = next(
        item for item in journeys["journeys"] if item["journey_id"] == "portfolio-cvar-allocation"
    )
    assert journey["status"] == "complete"
    assert journey["completion_reasons"] == []
