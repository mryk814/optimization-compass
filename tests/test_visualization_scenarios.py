from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.surrogate_uncertainty import (
    Observation,
    canonical_renderer_bytes,
    generate_evaluation_ledger_scenario,
    generate_high_fidelity_baseline_scenario,
    generate_low_fidelity_bias_scenario,
    generate_surrogate_scenario,
)
from optimization_compass.visualization_scenarios import VisualizationScenarioIndex

FIXTURE = Path("site/src/contracts/visualization-scenarios.fixture.json")


def test_shared_visualization_scenario_fixture_is_valid() -> None:
    index = VisualizationScenarioIndex.model_validate_json(FIXTURE.read_bytes())

    assert index.contract_version == "1.2.0"
    assert index.scenarios[0].artifact.renderer_family == "simplex_geometry"
    assert index.scenarios[0].lesson.limitations_ja == "2次元の教育用決定論的実行"
    assert index.scenarios[0].lesson.primary_observables
    assert index.scenarios[0].lesson.narration_steps[0].milestone_id == "start"


def test_visualization_scenario_rejects_unknown_envelope_fields() -> None:
    payload = VisualizationScenarioIndex.model_validate_json(FIXTURE.read_bytes()).model_dump(
        mode="json"
    )
    payload["renderer_registry"] = {}

    with pytest.raises(ValidationError, match="extra_forbidden"):
        VisualizationScenarioIndex.model_validate(payload)


def test_surrogate_scenario_is_deterministic_and_uses_the_shared_envelope() -> None:
    first = generate_surrogate_scenario(
        dataset_version="0.3.0", strategy="explore", noise_preset="noiseless"
    )
    second = generate_surrogate_scenario(
        dataset_version="0.3.0", strategy="explore", noise_preset="noiseless"
    )

    assert first.payload_bytes == second.payload_bytes
    assert first.scenario.purpose == "mechanism"
    assert first.scenario.artifact.renderer_family == "surrogate_uncertainty"
    assert first.scenario.artifact.payload_path == "visualizations/bo-explore-noiseless.json"
    assert first.payload.frames[-1].oracle_evaluations == first.scenario.experiment.budget.value
    assert len(first.payload.random_history) == first.scenario.experiment.budget.value


def test_renderer_serialization_removes_platform_float_noise() -> None:
    first = Observation(x=0.123456789012341, value=1.0, observed_value=2.0)
    second = Observation(x=0.123456789012349, value=1.0, observed_value=2.0)
    negligible = Observation(x=8e-10, value=1.0, observed_value=2.0)

    assert canonical_renderer_bytes(first) == canonical_renderer_bytes(second)
    assert b'"x":0.12345679' in canonical_renderer_bytes(first)
    assert b'"x":0.0' in canonical_renderer_bytes(negligible)


def test_surrogate_variants_are_sensitivity_scenarios() -> None:
    variants = [
        generate_surrogate_scenario(dataset_version="0.3.0", strategy=strategy, noise_preset=noise)
        for strategy, noise in (
            ("exploit", "noiseless"),
            ("exploit", "small_noise"),
            ("explore", "small_noise"),
        )
    ]

    assert {item.scenario.purpose for item in variants} == {"sensitivity"}
    assert len({item.scenario.scenario_id for item in variants}) == 3
    assert all(item.scenario.lesson.misconception for item in variants)
    assert all(item.scenario.lesson.failure_signals for item in variants)


def test_evaluation_ledger_scenario_preserves_cost_fidelity_and_failure_statuses() -> None:
    first = generate_evaluation_ledger_scenario(dataset_version="0.3.0")
    second = generate_evaluation_ledger_scenario(dataset_version="0.3.0")
    ledger = first.payload.evaluation_ledger

    assert first.payload_bytes == second.payload_bytes
    assert first.scenario.scenario_id == "SCENARIO_BO_1D_MULTIFIDELITY_LEDGER"
    assert first.scenario.experiment.parameter_preset_id == "BO_1D_MULTIFIDELITY_LEDGER"
    assert first.scenario.artifact.artifact_contract_version == "1.1.0"
    assert ledger is not None
    assert {call.fidelity for call in ledger.calls} == {"low", "high"}
    assert {call.status for call in ledger.calls} == {"ok", "failed", "censored", "timeout"}
    assert ledger.calls[-1].accumulated_cost == ledger.budget_cost == 36.0
    assert ledger.calls[-1].accumulated_high_fidelity_equivalent_cost == 3.0
    assert ledger.calls[-1].best_so_far is not None
    assert "does not establish" in first.scenario.lesson.limitations_en


def test_cost_aligned_baseline_uses_the_same_initial_design_and_budget() -> None:
    mixed = generate_evaluation_ledger_scenario(dataset_version="0.3.0")
    baseline = generate_high_fidelity_baseline_scenario(dataset_version="0.3.0")
    mixed_ledger = mixed.payload.evaluation_ledger
    baseline_ledger = baseline.payload.evaluation_ledger

    assert mixed_ledger is not None and baseline_ledger is not None
    assert [call.x for call in mixed_ledger.calls[:3]] == [call.x for call in baseline_ledger.calls]
    assert {call.fidelity for call in baseline_ledger.calls} == {"high"}
    assert mixed_ledger.budget_cost == baseline_ledger.budget_cost == 36.0
    assert (
        mixed_ledger.high_fidelity_equivalent_budget
        == baseline_ledger.high_fidelity_equivalent_budget
        == 3.0
    )
    assert mixed_ledger.calls[-1].accumulated_cost == baseline_ledger.calls[-1].accumulated_cost
    assert baseline.scenario.lesson.comparison_role == "baseline"
    assert (
        baseline.scenario.experiment.parameter_preset_id
        == baseline.scenario.scenario_id.removeprefix("SCENARIO_")
    )


def test_low_fidelity_bias_scenario_reverses_the_two_candidate_ordering() -> None:
    generated = generate_low_fidelity_bias_scenario(dataset_version="0.3.0")
    ledger = generated.payload.evaluation_ledger

    assert ledger is not None
    values = {(call.x, call.fidelity): call.observed_value for call in ledger.calls}
    assert values[(-1.1, "low")] < values[(0.5, "low")]
    assert values[(-1.1, "high")] > values[(0.5, "high")]
    assert generated.scenario.purpose == "failure_contrast"
    assert generated.scenario.lesson.comparison_role == "failure_contrast"
    assert [signal.signal_id for signal in generated.scenario.lesson.failure_signals] == [
        "low_high_candidate_order_reverses"
    ]
    assert "observed_value" in generated.scenario.artifact.observable_ids


def test_established_scenario_identity_and_artifact_path_remain_stable() -> None:
    generated = VisualizationScenarioIndex.model_validate_json(
        Path("site/public/data/visualization-scenarios.json").read_bytes()
    )
    identities = {
        scenario.scenario_id: scenario.artifact.payload_path for scenario in generated.scenarios
    }

    assert identities["SCENARIO_NM_QUADRATIC"] == "traces/nelder-mead-quadratic.json"
    assert identities["SCENARIO_GD_QUADRATIC"] == "traces/gradient_descent-quadratic.json"
    assert identities["SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE"] == (
        "traces/binary-knapsack-bnb-complete.json"
    )
    assert identities["SCENARIO_BO_1D_EXPLORE_NOISELESS"] == (
        "visualizations/bo-explore-noiseless.json"
    )


def test_generated_lessons_cover_observables_signals_and_derived_text() -> None:
    generated = VisualizationScenarioIndex.model_validate_json(
        Path("site/public/data/visualization-scenarios.json").read_bytes()
    )

    assert all(scenario.lesson.learning_objective.ja for scenario in generated.scenarios)
    assert all(scenario.lesson.primary_observables for scenario in generated.scenarios)
    assert all(scenario.lesson.static_summary.ja for scenario in generated.scenarios)
    assert all(scenario.lesson.text_alternative.ja for scenario in generated.scenarios)
    assert all(scenario.lesson.derived_media_caption.ja for scenario in generated.scenarios)
    assert all(
        [step.milestone_id for step in scenario.lesson.narration_steps]
        == ["start", "first_change", "pattern_visible", "termination"]
        for scenario in generated.scenarios
    )
    guided = [scenario for scenario in generated.scenarios if scenario.guided_story is not None]
    assert {scenario.artifact.renderer_family for scenario in guided} == {
        "simplex_geometry",
        "continuous_trajectory",
        "search_tree",
        "surrogate_uncertainty",
    }
    for scenario in guided:
        story = scenario.guided_story
        assert story is not None
        assert [step.frame_index for step in story.steps] == sorted(
            step.frame_index for step in story.steps
        )
    failure_or_sensitivity = [
        scenario
        for scenario in generated.scenarios
        if scenario.purpose in {"failure_contrast", "sensitivity"}
    ]
    assert all(scenario.lesson.misconception for scenario in failure_or_sensitivity)
    assert all(scenario.lesson.failure_signals for scenario in failure_or_sensitivity)
