from __future__ import annotations

from hashlib import sha256

from optimization_compass.visualization_scenarios import (
    VisualizationScenario,
    VisualizationScenarioIndex,
    canonical_scenario_bytes,
    generate_bo_scenario,
    write_visualization_scenarios,
)


def test_bo_scenario_is_reproducible_and_updates_surrogate() -> None:
    first = generate_bo_scenario(
        dataset_version="0.3.0", strategy="explore", noise_preset="noiseless"
    )
    second = generate_bo_scenario(
        dataset_version="0.3.0", strategy="explore", noise_preset="noiseless"
    )

    assert canonical_scenario_bytes(first) == canonical_scenario_bytes(second)
    assert first.payload.seed == 2604
    assert first.payload.acquisition_id == "expected_improvement"
    assert [frame.oracle_evaluations for frame in first.payload.frames] == list(range(3, 11))
    assert len(first.payload.frames[0].observations) == 3
    assert len(first.payload.frames[-1].observations) == 10
    assert first.payload.frames[0].predictive_summary != first.payload.frames[1].predictive_summary
    assert first.payload.frames[0].selected_acquisition is not None
    assert first.payload.frames[-1].selected_point is None
    assert len(first.payload.random_history) == first.payload.evaluation_budget
    assert first.payload.fairness.budget == first.payload.evaluation_budget


def test_exploration_and_noise_presets_change_generated_run() -> None:
    exploit = generate_bo_scenario(
        dataset_version="0.3.0", strategy="exploit", noise_preset="noiseless"
    )
    explore = generate_bo_scenario(
        dataset_version="0.3.0", strategy="explore", noise_preset="noiseless"
    )
    noisy = generate_bo_scenario(
        dataset_version="0.3.0", strategy="explore", noise_preset="small_noise"
    )

    assert exploit.payload.exploration_xi == 0
    assert explore.payload.exploration_xi > 0
    assert exploit.payload.frames[0].selected_point != explore.payload.frames[0].selected_point
    assert noisy.payload.noise_std > 0
    assert any(item.value != item.observed_value for item in noisy.payload.frames[0].observations)


def test_writer_emits_hashed_common_index(tmp_path) -> None:
    path, size, digest = write_visualization_scenarios(tmp_path, dataset_version="0.3.0")
    index_bytes = (tmp_path / path).read_bytes()
    index = VisualizationScenarioIndex.model_validate_json(index_bytes)

    assert size == len(index_bytes)
    assert digest == sha256(index_bytes).hexdigest()
    assert len(index.scenarios) == 4
    for entry in index.scenarios:
        artifact_bytes = (tmp_path / "visualizations" / entry.path).read_bytes()
        VisualizationScenario.model_validate_json(artifact_bytes)
        assert entry.bytes == len(artifact_bytes)
        assert entry.sha256 == sha256(artifact_bytes).hexdigest()
