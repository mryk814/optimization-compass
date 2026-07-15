from __future__ import annotations

from hashlib import sha256

from optimization_compass.learning_slices import (
    CONSTRAINED_ARTIFACT_ID,
    CONSTRAINED_SCENARIO_ID,
    PARETO_ARTIFACT_ID,
    PARETO_SCENARIO_ID,
    generate_feasible_region_artifact,
    generate_pareto_front_artifact,
    validate_reference_geometry,
    write_learning_slice_scenarios,
)


def test_feasible_region_trace_separates_objective_and_feasibility() -> None:
    artifact = generate_feasible_region_artifact("0.10.0")

    validate_reference_geometry()
    primary = next(path for path in artifact.paths if path.role == "constraint_aware")
    failure = next(path for path in artifact.paths if path.role == "unconstrained_failure")
    assert primary.steps[-1].active_constraint
    assert primary.steps[-1].violation == 0
    assert failure.steps[-1].objective < primary.steps[-1].objective
    assert not failure.steps[-1].feasible
    assert failure.steps[-1].violation > 0
    assert artifact.known_reference["point"] == list(artifact.best_feasible_point)


def test_pareto_result_is_deterministic_and_contains_dominance_contrast() -> None:
    first = generate_pareto_front_artifact("0.10.0")
    second = generate_pareto_front_artifact("0.10.0")

    assert first == second
    assert len(first.points) == 81
    assert any(point.dominated for point in first.points)
    assert all(not point.dominated for point in first.pareto_front)
    assert first.reference.ideal == (0.0, 0.0)
    assert not first.reference.ideal_is_feasible
    assert [selection.weight_f1 for selection in first.preference_selections] == [0.2, 0.5, 0.8]


def test_learning_slice_writer_closes_payload_hashes_and_routes(tmp_path) -> None:
    scenarios, links = write_learning_slice_scenarios(tmp_path, dataset_version="0.10.0")

    assert {scenario.scenario_id for scenario in scenarios} == {
        CONSTRAINED_SCENARIO_ID,
        PARETO_SCENARIO_ID,
    }
    assert {scenario.artifact.renderer_family for scenario in scenarios} == {
        "feasible_region",
        "pareto_front",
    }
    assert {link.artifact_id for link in links} == {
        CONSTRAINED_ARTIFACT_ID,
        PARETO_ARTIFACT_ID,
    }
    for scenario in scenarios:
        payload = tmp_path / scenario.artifact.payload_path
        assert payload.stat().st_size == scenario.artifact.payload_bytes
        assert sha256(payload.read_bytes()).hexdigest() == scenario.artifact.payload_sha256
        link = next(item for item in links if item.artifact_id == scenario.runs[0].artifact_id)
        assert link.route == f"/theater/learning/{scenario.scenario_id}"
