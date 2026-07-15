from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.surrogate_uncertainty import (
    Observation,
    canonical_renderer_bytes,
    generate_surrogate_scenario,
)
from optimization_compass.visualization_scenarios import VisualizationScenarioIndex

FIXTURE = Path("site/src/contracts/visualization-scenarios.fixture.json")


def test_shared_visualization_scenario_fixture_is_valid() -> None:
    index = VisualizationScenarioIndex.model_validate_json(FIXTURE.read_bytes())

    assert index.contract_version == "1.1.0"
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
    failure_or_sensitivity = [
        scenario
        for scenario in generated.scenarios
        if scenario.purpose in {"failure_contrast", "sensitivity"}
    ]
    assert all(scenario.lesson.misconception for scenario in failure_or_sensitivity)
    assert all(scenario.lesson.failure_signals for scenario in failure_or_sensitivity)
