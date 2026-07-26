from __future__ import annotations

import ast
import json
import sqlite3
from pathlib import Path

from optimization_compass.dataset_release import build_staged_release

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"


def test_topology_cantilever_connects_formulation_to_visual_diagnostics() -> None:
    gallery = json.loads(Path("data/seeds/site_gallery.json").read_text(encoding="utf-8"))
    case = next(item for item in gallery["cases"] if item["case_id"] == "topology-cantilever")

    assert case["problem_archetype_id"] == "PA045"
    assert case["map_node_id"] == "answer:Q01:continuous"
    assert {
        "SCENARIO_TOPOLOGY_SIMP_OC",
        "SCENARIO_TOPOLOGY_CHECKERBOARD",
        "SCENARIO_TOPOLOGY_OC_MMA_COMPARISON",
    } <= set(case["visualization_ids"])
    assert case["comparison_ids"] == ["COMPARE_TOPOLOGY_OC_MMA"]
    ast.parse(case["python_example"])
    assert "generate_topology_field_artifact" in case["python_example"]
    assert "checkerboard_score" in case["python_example"]
    assert "derived state" in case["decision_variables"]
    assert "①density" in case["practical_notes"]
    assert "④gray fraction" in case["practical_notes"]
    assert "OCとMMAの比較" in case["practical_notes"]
    assert "Q4 FEM解析値" in case["limitations"][0]
    assert case["implementation_ids"] == ["I_TOPOPT_88_MATLAB"]


def test_topopt_88_mapping_is_bounded_to_the_documented_teaching_workflow(
    tmp_path: Path,
) -> None:
    staged = build_staged_release(BASE_DATABASE, tmp_path / "release")
    with sqlite3.connect(staged.database_path) as connection:
        implementation = connection.execute(
            """
            SELECT library_name, license, open_source, supported_method_ids, source_ids
            FROM implementations
            WHERE implementation_id = 'I_TOPOPT_88_MATLAB'
            """
        ).fetchone()
        mappings = connection.execute(
            """
            SELECT method_id, support_level
            FROM method_implementation_map
            WHERE implementation_id = 'I_TOPOPT_88_MATLAB'
            ORDER BY method_id
            """
        ).fetchall()

    assert implementation == (
        "DTU TopOpt",
        "source-specific terms; not stated on the official download page",
        "unknown",
        "M_SIMP_TOPOLOGY;M_DENSITY_FILTER;M_OC_TOPOLOGY",
        "S097;S098;S099",
    )
    assert mappings == [
        ("M_DENSITY_FILTER", "native"),
        ("M_OC_TOPOLOGY", "native"),
        ("M_SIMP_TOPOLOGY", "native"),
    ]
