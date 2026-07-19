from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.comparisons import (
    ComparisonIndex,
    load_comparison_seed,
    validate_comparison_benchmark_contexts,
)
from optimization_compass.constraint_geometry import (
    EVALUATION_BUDGET,
    GENERATOR_ID,
    GENERATOR_VERSION,
    PROFILE_ID,
    PROJECTED_SCENARIO_ID,
    RIEMANNIAN_SCENARIO_ID,
    build_so3_scenario,
    generate_so3_traces,
)
from optimization_compass.dataset_release import build_staged_release
from optimization_compass.problem_registry import get_runtime_problem
from optimization_compass.trace_models import TraceFrame
from optimization_compass.visualization_scenarios import scenario_identity

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"


def _metric(frame: TraceFrame, metric_id: str) -> float:
    return next(metric.value for metric in frame.metrics if metric.metric_id == metric_id)


def _so3_context() -> dict[str, object]:
    return {
        "context_id": "BENCH_SO3_ATTITUDE_FIXED_12",
        "problem_instance_id": "INSTANCE_SO3_ATTITUDE_FIXED_3",
        "evaluation_budget": EVALUATION_BUDGET,
        "runtime": {
            "comparison_scope": "exact",
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
        },
        "implementation_versions": {
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
            "implementation_mapping_status": "not_applicable",
        },
        "initialization": {
            "policy": "fixed_matrix",
            "points": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        },
        "oracle_budget": {"limit": EVALUATION_BUDGET, "unit": "oracle_evaluations"},
        "stopping": {"policy": "fixed_oracle_budget", "value": EVALUATION_BUDGET},
        "seed_status": "not_applicable",
        "seed_value": None,
    }


def test_so3_generators_reduce_loss_while_preserving_rotation_structure() -> None:
    traces = generate_so3_traces(dataset_version="0.18.7")

    assert {trace.profile_id for trace in traces} == {PROFILE_ID}
    assert {trace.evaluation_budget for trace in traces} == {EVALUATION_BUDGET}
    assert {trace.generator_id for trace in traces} == {GENERATOR_ID}
    for trace in traces:
        assert len(trace.frames) == EVALUATION_BUDGET + 1
        assert _metric(trace.frames[-1], "objective_value") < _metric(
            trace.frames[0], "objective_value"
        )
        assert _metric(trace.frames[-1], "geodesic_residual") < _metric(
            trace.frames[0], "geodesic_residual"
        )
        assert _metric(trace.frames[-1], "orthogonality_error") < 1e-12
        assert _metric(trace.frames[-1], "determinant_error") < 1e-12


def test_so3_primary_scenario_is_canonical_and_projection_is_derived() -> None:
    scenarios = {
        trace.scenario_id: build_so3_scenario(trace)
        for trace in generate_so3_traces(dataset_version="0.18.7")
    }

    assert scenario_identity(RIEMANNIAN_SCENARIO_ID) == (
        "canonical",
        RIEMANNIAN_SCENARIO_ID,
    )
    assert scenario_identity(PROJECTED_SCENARIO_ID) == (
        "derived",
        RIEMANNIAN_SCENARIO_ID,
    )
    assert scenarios[RIEMANNIAN_SCENARIO_ID].identity_status == "canonical"
    assert scenarios[RIEMANNIAN_SCENARIO_ID].purpose == "mechanism"
    assert scenarios[PROJECTED_SCENARIO_ID].identity_status == "derived"
    assert scenarios[PROJECTED_SCENARIO_ID].purpose == "sensitivity"
    assert {scenario.artifact.renderer_family for scenario in scenarios.values()} == {
        "generic_metric_history"
    }


def test_so3_comparison_matches_the_exact_fixed_context() -> None:
    index = load_comparison_seed(ROOT / "data/seeds/site_comparisons.json", "0.18.7")
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_SO3_PROJECTED_RIEMANNIAN"
    )
    so3_index = ComparisonIndex(dataset_version=index.dataset_version, comparisons=[comparison])
    traces = generate_so3_traces(dataset_version=index.dataset_version)
    scenarios = [build_so3_scenario(trace) for trace in traces]
    context = _so3_context()

    validate_comparison_benchmark_contexts(
        so3_index,
        [context],
        scenarios,
        problem_definition_ids={"PROBLEM_SO3_ATTITUDE_ALIGNMENT"},
        problem_instance_ids={"INSTANCE_SO3_ATTITUDE_FIXED_3"},
        traces=traces,
    )
    # The shared #135 authority must also resolve the SO(3) profile without a trace lookup.
    validate_comparison_benchmark_contexts(so3_index, [context], scenarios)

    context["problem_instance_id"] = "OBJECTIVE_QUADRATIC_2D"
    with pytest.raises(ValueError, match="different problem instance"):
        validate_comparison_benchmark_contexts(so3_index, [context], scenarios)


def test_so3_case_problem_and_secondary_spd_content_close_the_declared_slice() -> None:
    gallery = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "so3-attitude-alignment")
    problem = get_runtime_problem("INSTANCE_SO3_ATTITUDE_FIXED_3")
    reference = problem.instance.known_reference

    assert case["problem_archetype_id"] == "PA037"
    assert set(case["question_answers"]) == {f"Q{index:02d}" for index in range(1, 13)}
    assert [item["method_id"] for item in case["candidate_methods"]] == ["M_RIEMANNIAN_GRADIENT"]
    assert {item["method_id"] for item in case["conditional_methods"]} == {
        "M_PROJECTED_GRADIENT",
        "M_RIEMANNIAN_TRUST_REGION",
    }
    assert set(case["implementation_ids"]) == {
        "I_PYMANOPT",
        "I_MANOPT_MATLAB",
        "I_MANOPT_JL",
    }
    assert case["comparison_ids"] == ["COMPARE_SO3_PROJECTED_RIEMANNIAN"]
    assert {"S044", "S045", "S071", "S107"} <= set(case["source_ids"])
    compile(case["python_example"], "so3-attitude-alignment", "exec")

    assert reference is not None
    assert problem.objective_value(reference["point"]) == pytest.approx(0.0)
    assert problem.objective_gradient(reference["point"]) == pytest.approx([0.0] * 9)

    spd = (ROOT / "content/concepts/spd-matrix-geometry.md").read_text(encoding="utf-8")
    for distinction in (
        "Cholesky",
        "matrix exponential",
        "PSD境界",
        "minimum eigenvalue",
        "condition number",
    ):
        assert distinction in spd
    assert "S108" in spd


def test_constraint_geometry_audit_keeps_the_eight_field_contract_and_followups() -> None:
    audit = (ROOT / "docs/research/constraint-geometry-contract-and-audit.md").read_text(
        encoding="utf-8"
    )

    for required_field in (
        "set and degrees of freedom",
        "naive Euclidean failure",
        "representations",
        "feasibility map",
        "boundary and non-uniqueness",
        "guarantee scope",
        "methods and implementations",
        "diagnostics",
    ):
        assert required_field in audit
    for followup in ("simplex", "SPD", "Stiefel / Grassmann", "SE(3)", "fixed-rank"):
        assert followup in audit
    assert "M_MIRROR_DESCENT" in audit
    assert "no direct implementation mapping" in audit


def test_staged_release_exports_a_complete_so3_learning_journey(tmp_path: Path) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    payload = json.loads(
        (release.site_data_directory / "learning-journeys.json").read_text(encoding="utf-8")
    )
    journey = next(
        item for item in payload["journeys"] if item["case_id"] == "so3-attitude-alignment"
    )

    assert journey["status"] == "complete"
    assert journey["completion_reasons"] == []
    assert journey["problem_instance_ids"] == ["INSTANCE_SO3_ATTITUDE_FIXED_3"]
    assert {item["role"] for item in journey["scenarios"]} == {"primary", "sensitivity"}
    assert [item["comparison_id"] for item in journey["comparisons"]] == [
        "COMPARE_SO3_PROJECTED_RIEMANNIAN"
    ]
