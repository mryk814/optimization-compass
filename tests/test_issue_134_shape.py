from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.comparisons import load_comparison_seed
from optimization_compass.problem_registry import get_runtime_problem, load_problem_suite
from optimization_compass.shape_optimization import (
    build_shape_optimization_scenario,
    generate_shape_optimization_traces,
)
from optimization_compass.visualization_scenarios import scenario_identity

ROOT = Path(__file__).parents[1]


def test_shape_problem_is_distinct_from_existing_topology_contract() -> None:
    suite = load_problem_suite()
    definitions = {item.problem_definition_id: item for item in suite.definitions}
    instances = {item.problem_instance_id: item for item in suite.instances}

    shape = definitions["PROBLEM_SHAPE_OPTIMIZATION"]
    diffuser = instances["INSTANCE_DIFFUSER_SHAPE_3P"]
    topology = definitions["PROBLEM_TOPOLOGY_OPTIMIZATION"]
    cantilever = instances["INSTANCE_TOPOLOGY_CANTILEVER_2D"]

    assert shape.mathematical_family == "shape_optimization"
    assert shape.related_problem_ids == ["PA057", "PA045"]
    assert diffuser.dimension == 3
    assert diffuser.parameters["topology_change_allowed"] is False
    assert topology.mathematical_family == "topology_optimization"
    assert topology.variable_domain == "field"
    assert cantilever.dimension == 32
    assert cantilever.registry_key == "problem.topology.cantilever.v1"


def test_diffuser_reduced_objective_and_gradient_are_deterministic() -> None:
    problem = get_runtime_problem("INSTANCE_DIFFUSER_SHAPE_3P")
    point = [1.15, 0.1, -0.05]

    assert problem.objective_value(point) == pytest.approx(0.095625)
    assert problem.objective_gradient(point) == pytest.approx([-0.585, 0.08, -0.02])


def test_shape_gallery_separates_parameter_geometry_mesh_and_state() -> None:
    payload = json.loads((ROOT / "data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in payload["cases"] if item["case_id"] == "shape-diffuser")

    assert case["problem_archetype_id"] == "PA057"
    assert [item["method_id"] for item in case["candidate_methods"]] == ["M_SLSQP"]
    assert {item["method_id"] for item in case["conditional_methods"]} == {
        "M_INTERIOR_POINT_NLP",
        "M_ADJOINT_SENSITIVITY",
    }
    assert [item["method_id"] for item in case["excluded_methods"]] == ["M_SIMP_TOPOLOGY"]
    for layer in ("parameter", "geometry", "mesh", "physical state"):
        assert layer in case["decision_variables"] or layer in case["practical_notes"]
    assert "topologyを固定" in case["decision_variables"]
    assert "CFD" in case["limitations"][0]
    for domain in ("構造", "CFD", "thermal", "acoustic", "photonic"):
        assert domain in case["practical_notes"]


def test_shape_theater_has_valid_primary_and_independent_geometry_failure() -> None:
    traces = generate_shape_optimization_traces(dataset_version="0.18.9")
    scenarios = {trace.scenario_id: build_shape_optimization_scenario(trace) for trace in traces}

    assert set(scenarios) == {
        "SCENARIO_SHAPE_DIFFUSER_VALID_UPDATE",
        "SCENARIO_SHAPE_DIFFUSER_INVALID_GEOMETRY",
        "SCENARIO_SHAPE_TOPOLOGY_REPRESENTATION_CONTRAST",
    }
    primary = scenarios["SCENARIO_SHAPE_DIFFUSER_VALID_UPDATE"]
    failure = scenarios["SCENARIO_SHAPE_DIFFUSER_INVALID_GEOMETRY"]
    assert primary.identity_status == "canonical"
    assert primary.problem_definition_id == "PROBLEM_SHAPE_OPTIMIZATION"
    assert primary.artifact.renderer_family == "generic_metric_history"
    assert failure.purpose == "failure_contrast"
    assert failure.lesson.comparison_role == "failure_contrast"
    assert scenario_identity("SCENARIO_SHAPE_DIFFUSER_INVALID_GEOMETRY") == (
        "derived",
        "SCENARIO_SHAPE_DIFFUSER_VALID_UPDATE",
    )
    final_failure = next(
        trace for trace in traces if trace.scenario_id == failure.scenario_id
    ).frames[-1]
    assert final_failure.payload["geometry"]["self_intersection"] is True
    assert final_failure.payload["mesh"]["inverted_cells"] > 0
    assert final_failure.metrics[-2].value < traces[0].frames[0].metrics[-2].value


def test_shape_topology_compare_is_exact_aligned_and_contrast_only() -> None:
    index = load_comparison_seed(
        ROOT / "data/seeds/site_comparisons.json", dataset_version="0.18.9"
    )
    comparison = next(
        item
        for item in index.comparisons
        if item.comparison_id == "COMPARE_SHAPE_TOPOLOGY_REPRESENTATION"
    )

    assert comparison.case_id == "shape-diffuser"
    assert comparison.problem_definition_id == "PROBLEM_SHAPE_OPTIMIZATION"
    assert comparison.problem_instance_id == "INSTANCE_DIFFUSER_SHAPE_3P"
    assert comparison.benchmark_context_id == "BENCH_SHAPE_TOPOLOGY_REPRESENTATION_6"
    assert comparison.comparability == "contrast_only"
    assert comparison.ranking_eligible is False
    assert comparison.budget.metric == comparison.synchronization_axis == "oracle_evaluations"
    assert all(member.budget == comparison.budget for member in comparison.members)
    assert {member.method_id for member in comparison.members} == {
        "M_SLSQP",
        "M_SIMP_TOPOLOGY",
    }
    assert comparison.changed_factors == [
        "design representation only: three bounded shape parameters with fixed topology "
        "versus a density field that permits connectivity change"
    ]


def test_shape_sources_and_content_routes_are_canonical() -> None:
    migration = (ROOT / "data/migrations/018_shape_optimization.sql").read_text(encoding="utf-8")
    assert "PA057" in migration
    assert "BENCH_SHAPE_TOPOLOGY_REPRESENTATION_6" in migration
    assert '"comparison_scope":"exact"' in migration
    assert "https://arxiv.org/abs/2010.02048" in migration
    assert "https://arxiv.org/abs/2306.09828" in migration
    assert "cashocs.readthedocs.io" in migration
    assert {"S104", "S105", "S106"} <= {
        row.split("'", 2)[1] for row in migration.splitlines() if row.strip().startswith("'S")
    }

    for content_id in (
        "shape-optimization",
        "shape-parameter-sensitivity",
        "geometry-update-failure-modes",
    ):
        text = (ROOT / f"content/concepts/{content_id}.md").read_text(encoding="utf-8")
        assert "shape-diffuser" in text or "shape-diffuser-valid-update" in text
        assert "COMPARE_SHAPE_TOPOLOGY_REPRESENTATION" in text
        assert "S104" in text
