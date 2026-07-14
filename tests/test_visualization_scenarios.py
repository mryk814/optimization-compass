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

    assert index.contract_version == "1.0.0"
    assert index.scenarios[0].artifact.renderer_family == "simplex_geometry"
    assert index.scenarios[0].lesson.limitations_ja == "2次元の教育用決定論的実行"


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
