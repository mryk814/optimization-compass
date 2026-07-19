from __future__ import annotations

from hashlib import sha256

from optimization_compass.learning_slices import (
    CONSTRAINED_ARTIFACT_ID,
    CONSTRAINED_FEASIBLE_PATH_SCENARIO_ID,
    CONSTRAINED_SCENARIO_ID,
    PARETO_ARTIFACT_ID,
    PARETO_PREFERENCE_SCENARIO_ID,
    PARETO_SCENARIO_ID,
    TOPOLOGY_ARTIFACT_ID,
    TOPOLOGY_COMPARISON_SCENARIO_ID,
    TOPOLOGY_FAILURE_SCENARIO_ID,
    TOPOLOGY_SCENARIO_ID,
    generate_feasible_region_artifact,
    generate_pareto_front_artifact,
    validate_reference_geometry,
    write_learning_slice_scenarios,
)
from optimization_compass.visualization_scenarios import scenario_identity


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
    lens = first.triobjective_lens
    assert len(lens.points) == 81
    assert lens.reference.status == "sampled_grid"
    assert any(point.dominated for point in lens.points)
    assert all(not point.dominated for point in lens.pareto_front)
    assert lens.objective_expressions[2] == "f₃=(x−2)²+y²"


def test_learning_slice_writer_closes_payload_hashes_and_routes(tmp_path) -> None:
    scenarios, links = write_learning_slice_scenarios(tmp_path, dataset_version="0.10.0")

    assert {scenario.scenario_id for scenario in scenarios} == {
        CONSTRAINED_FEASIBLE_PATH_SCENARIO_ID,
        CONSTRAINED_SCENARIO_ID,
        PARETO_PREFERENCE_SCENARIO_ID,
        PARETO_SCENARIO_ID,
        TOPOLOGY_SCENARIO_ID,
        TOPOLOGY_FAILURE_SCENARIO_ID,
        TOPOLOGY_COMPARISON_SCENARIO_ID,
    }
    assert {scenario.artifact.renderer_family for scenario in scenarios} == {
        "feasible_region",
        "pareto_front",
        "field_evolution",
    }
    assert {link.artifact_id for link in links} == {
        CONSTRAINED_ARTIFACT_ID,
        PARETO_ARTIFACT_ID,
        TOPOLOGY_ARTIFACT_ID,
    }
    for scenario in scenarios:
        payload = tmp_path / scenario.artifact.payload_path
        assert payload.stat().st_size == scenario.artifact.payload_bytes
        assert sha256(payload.read_bytes()).hexdigest() == scenario.artifact.payload_sha256

    mechanism = next(
        scenario
        for scenario in scenarios
        if scenario.scenario_id == CONSTRAINED_FEASIBLE_PATH_SCENARIO_ID
    )
    assert mechanism.identity_status == "derived"
    assert mechanism.canonical_scenario_id == CONSTRAINED_SCENARIO_ID
    assert mechanism.purpose == "mechanism"
    assert [run.run_id for run in mechanism.runs] == ["RUN_CONSTRAINED_AWARE"]
    assert mechanism.lesson.recommended_next_scenario_ids == [CONSTRAINED_SCENARIO_ID]
    assert scenario_identity(CONSTRAINED_FEASIBLE_PATH_SCENARIO_ID) == (
        "derived",
        CONSTRAINED_SCENARIO_ID,
    )

    comparison = next(
        scenario
        for scenario in scenarios
        if scenario.scenario_id == TOPOLOGY_COMPARISON_SCENARIO_ID
    )
    assert comparison.purpose == "comparison"
    assert [run.method_id for run in comparison.runs] == ["M_OC_TOPOLOGY", "M_MMA"]
    assert scenario_identity(TOPOLOGY_COMPARISON_SCENARIO_ID) == (
        "derived",
        TOPOLOGY_SCENARIO_ID,
    )
    constrained_link = next(item for item in links if item.artifact_id == CONSTRAINED_ARTIFACT_ID)
    assert constrained_link.route == f"/theater/learning/{CONSTRAINED_SCENARIO_ID}"

    preference = next(
        scenario for scenario in scenarios if scenario.scenario_id == PARETO_PREFERENCE_SCENARIO_ID
    )
    assert preference.identity_status == "derived"
    assert preference.canonical_scenario_id == PARETO_SCENARIO_ID
    assert preference.purpose == "sensitivity"
    assert (
        preference.artifact
        == next(
            scenario for scenario in scenarios if scenario.scenario_id == PARETO_SCENARIO_ID
        ).artifact
    )
    primary = next(scenario for scenario in scenarios if scenario.scenario_id == PARETO_SCENARIO_ID)
    assert preference.runs == primary.runs
    assert [(run.method_id, run.profile_id, run.artifact_id) for run in preference.runs] == [
        ("M_NSGA_II", "PROFILE_NSGA_II_PARETO_FRONT", PARETO_ARTIFACT_ID)
    ]
    assert scenario_identity(PARETO_PREFERENCE_SCENARIO_ID) == (
        "derived",
        PARETO_SCENARIO_ID,
    )
