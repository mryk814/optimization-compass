from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.dataset_release import build_staged_release
from optimization_compass.metadata_models import AtlasMetadataSeed

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"
SEED_PATH = ROOT / "data/seeds/atlas_metadata.json"


@pytest.fixture()
def staged_database(tmp_path: Path) -> Path:
    result = build_staged_release(BASE_DATABASE, tmp_path / "release")
    return result.database_path


def test_seed_is_explicit_and_closes_all_references() -> None:
    seed = AtlasMetadataSeed.model_validate_json(SEED_PATH.read_text(encoding="utf-8"))

    assert {preset.family for preset in seed.view_presets} == {
        "semantic_tree",
        "algorithm_theater",
        "comparison",
    }
    assert {profile.method_id for profile in seed.method_visualization_profiles} == {
        "M_NELDER_MEAD",
        "M_GRADIENT_DESCENT",
        "M_MOMENTUM_SGD",
        "M_ADAM",
    }
    assert all(
        profile.implementation_status == "not_applicable"
        for profile in seed.method_visualization_profiles
    )
    assert all(profile.implementation_id is None for profile in seed.method_visualization_profiles)
    assert len(seed.demo_scenarios) == 2
    assert len(seed.comparison_sets) == 1
    assert len(seed.comparison_set_members) == 3
    assert seed.learning_edges


def test_seed_rejects_duplicate_relation_values() -> None:
    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    payload["view_presets"][0]["relation_types"].append(
        payload["view_presets"][0]["relation_types"][0]
    )

    with pytest.raises(ValidationError, match="duplicate"):
        AtlasMetadataSeed.model_validate(payload)


def test_schema_enforces_conditional_support_and_member_uniqueness(
    staged_database: Path,
) -> None:
    connection = sqlite3.connect(staged_database)
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO view_presets (
                  preset_id, family, name_ja, name_en, description_ja, description_en,
                  root_support_status, root_entity_type, root_entity_id, axis,
                  relation_types_json, max_depth, source_ids_json, last_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "V_BAD",
                    "semantic_tree",
                    "不正",
                    "Invalid",
                    "不正",
                    "Invalid",
                    "supported",
                    None,
                    None,
                    "problem_structure",
                    '["related"]',
                    1,
                    '["S001"]',
                    "2026-07-13",
                ),
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO comparison_set_members (
                  comparison_set_id, member_id, method_id, profile_id, label,
                  display_order, parameters_json
                ) SELECT comparison_set_id, 'duplicate-order', method_id, profile_id,
                         'duplicate', display_order, parameters_json
                  FROM comparison_set_members LIMIT 1
                """
            )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO method_visualization_profiles (
                  profile_id, method_id, family, support_status, min_dimension,
                  max_dimension, generator_id, implementation_status,
                  implementation_id, state_fields_json, event_types_json,
                  source_ids_json, last_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "P_BLANK",
                    "M_NELDER_MEAD",
                    "simplex_2d",
                    "supported",
                    2,
                    2,
                    " ",
                    "not_applicable",
                    None,
                    '["x"]',
                    '["step"]',
                    '["S001"]',
                    "2026-07-13",
                ),
            )
    finally:
        connection.close()


def test_staged_database_has_atlas_checks_and_closed_learning_edges(
    staged_database: Path,
) -> None:
    connection = sqlite3.connect(staged_database)
    try:
        check_rows = connection.execute(
            "SELECT check_id, status, checked_at FROM release_checks ORDER BY check_id"
        ).fetchall()
        unresolved = connection.execute(
            """
            SELECT COUNT(*)
            FROM learning_edges AS edge
            LEFT JOIN methods AS source_method
              ON edge.source_type = 'method' AND edge.source_id = source_method.method_id
            LEFT JOIN methods AS target_method
              ON edge.target_type = 'method' AND edge.target_id = target_method.method_id
            WHERE edge.source_type = 'method'
              AND (source_method.method_id IS NULL OR target_method.method_id IS NULL)
            """
        ).fetchone()[0]
    finally:
        connection.close()

    assert [row[0] for row in check_rows] == [f"CHK{index:03d}" for index in range(1, 21)]
    assert not [row for row in check_rows if row[1] == "fail"]
    assert {row[2] for row in check_rows} == {"2026-07-13"}
    assert unresolved == 0
