from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from optimization_compass.dataset_release import build_staged_release
from optimization_compass.db import KnowledgeRepository
from optimization_compass.problem_instances import ProblemSuiteSeed
from optimization_compass.problem_registry import get_runtime_problem, load_problem_suite

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"
PROBLEM_SEED = ROOT / "src/optimization_compass/resources/problem-suite.json"


def test_problem_suite_has_seventeen_closed_representative_instances() -> None:
    suite = ProblemSuiteSeed.model_validate_json(PROBLEM_SEED.read_text(encoding="utf-8"))

    assert suite == load_problem_suite()
    assert len(suite.instances) == 17
    assert {item.known_reference_status for item in suite.instances} >= {
        "known_exact",
        "unknown",
    }
    assert {
        "OBJECTIVE_QUADRATIC_2D",
        "OBJECTIVE_ROSENBROCK_2D",
        "OBJECTIVE_EDUCATIONAL_WAVY_1D",
        "INSTANCE_BINARY_KNAPSACK_4",
        "INSTANCE_CONSTRAINED_DISK_2D",
        "INSTANCE_BIOBJECTIVE_QUADRATIC_2D",
        "INSTANCE_EXPONENTIAL_DECAY_FIT_3P",
        "INSTANCE_OPTIMAL_CONTROL_EC020",
        "INSTANCE_PENDULUM_SWING_UP_EC020",
        "INSTANCE_PORTFOLIO_CVAR_FIXED_8_4",
        "INSTANCE_BILEVEL_REGRESSION_2COEF",
        "INSTANCE_HYBRID_CHATTERING_LEDGER",
    } <= {item.problem_instance_id for item in suite.instances}
    assert all(item.display.get("range") for item in suite.instances)
    assert all(item.display.get("axis_labels") for item in suite.instances)
    assert all(item.display.get("units") for item in suite.instances)
    direction_by_definition = {
        item.problem_definition_id: item.objective_direction for item in suite.definitions
    }
    assert all(direction_by_definition[item.problem_definition_id] for item in suite.instances)
    for instance in suite.instances:
        if instance.known_reference is not None:
            assert instance.known_reference["source_ids"]


@pytest.mark.parametrize(
    ("instance_id", "point", "expected"),
    [
        ("INSTANCE_QUADRATIC_ISOTROPIC_2D", [0.0, 0.0], 0.0),
        ("OBJECTIVE_QUADRATIC_2D", [0.0, 0.0], 0.0),
        ("OBJECTIVE_ROSENBROCK_2D", [1.0, 1.0], 0.0),
        ("INSTANCE_RASTRIGIN_2D", [0.0, 0.0], 0.0),
        ("INSTANCE_ABSOLUTE_RIDGE_2D", [0.0, 0.0], 0.0),
        ("INSTANCE_BINARY_KNAPSACK_4", [1.0, 1.0, 0.0, 0.0], 15.0),
        ("INSTANCE_ASSIGNMENT_3X3", [1.0, 0.0, 2.0], 5.0),
        (
            "INSTANCE_CONSTRAINED_DISK_2D",
            [0.2928932188134524, 0.2928932188134524],
            0.1715728752538099,
        ),
        ("INSTANCE_EXPONENTIAL_DECAY_FIT_3P", [1.8, 0.7, 0.25], 0.0),
        ("INSTANCE_PORTFOLIO_CVAR_FIXED_8_4", [0.3, 0.4, 0.0, 0.3], -0.0055),
    ],
)
def test_registry_reproduces_scalar_known_references(
    instance_id: str, point: list[float], expected: float
) -> None:
    value = get_runtime_problem(instance_id).objective_value(point)

    assert isinstance(value, float)
    assert value == pytest.approx(expected)


def test_registry_reproduces_biobjective_reference_endpoints() -> None:
    problem = get_runtime_problem("INSTANCE_BIOBJECTIVE_QUADRATIC_2D")

    assert problem.objective_value([0.0, 0.0]) == pytest.approx((0.0, 8.0))
    assert problem.objective_value([2.0, 2.0]) == pytest.approx((8.0, 0.0))


def test_registry_reproduces_optimal_control_educational_objective() -> None:
    problem = get_runtime_problem("INSTANCE_OPTIMAL_CONTROL_EC020")

    assert problem.objective_value([0.0] * 60) == pytest.approx(1.0)


def test_registry_reproduces_pendulum_terminal_penalty() -> None:
    problem = get_runtime_problem("INSTANCE_PENDULUM_SWING_UP_EC020")

    assert problem.objective_value([0.0] * 60) == pytest.approx(20.0 * 3.141592653589793**2)


def test_registry_executes_nested_and_hybrid_teaching_instances() -> None:
    nested = get_runtime_problem("INSTANCE_BILEVEL_REGRESSION_2COEF")
    hybrid = get_runtime_problem("INSTANCE_HYBRID_CHATTERING_LEDGER")

    assert nested.objective_value([0.2]) == pytest.approx(0.0009048546)
    assert hybrid.objective_value([0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]) == 0.0


def test_staged_sqlite_and_generated_catalog_share_one_authority(tmp_path: Path) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    repository = KnowledgeRepository(release.database_path)

    catalog = repository.problem_catalog()
    assert len(catalog.definitions) == 15
    assert len(catalog.instances) == 17
    context = next(
        item
        for item in repository.benchmark_contexts()
        if item["context_id"] == "BENCH_BILEVEL_REGRESSION_EDUCATIONAL_6"
    )
    assert context["problem_instance_id"] == "INSTANCE_BILEVEL_REGRESSION_2COEF"
    assert (release.site_data_directory / "problems.json").read_text(encoding="utf-8")


def test_existing_visualization_families_resolve_canonical_instances() -> None:
    catalog = load_problem_suite()
    instance_ids = {item.problem_instance_id for item in catalog.instances}
    scenarios = json.loads(
        (ROOT / "site/public/data/visualization-scenarios.json").read_text(encoding="utf-8")
    )["scenarios"]
    expected_families = {
        "simplex_geometry",
        "continuous_trajectory",
        "search_tree",
        "surrogate_uncertainty",
        "generic_metric_history",
    }
    resolved = {
        scenario["artifact"]["renderer_family"]: scenario["problem_instance_id"]
        for scenario in scenarios
        if scenario["artifact"]["renderer_family"] in expected_families
    }

    assert set(resolved) == expected_families
    assert set(resolved.values()) <= instance_ids


def test_renderers_do_not_own_optimum_or_display_ranges() -> None:
    production_files = [
        *ROOT.glob("site/src/features/visualization/*.ts*"),
        *ROOT.glob("site/src/features/theater/*.ts*"),
        *ROOT.glob("site/src/features/search-tree/*.ts*"),
        *ROOT.glob("site/src/features/playback/*.ts*"),
        *ROOT.glob("site/src/features/compare/*.ts*"),
    ]
    forbidden = re.compile(r"(?:display_range|known_reference|optimum)\s*[:=]\s*\{")

    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in production_files
        if ".test." not in path.name and forbidden.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
