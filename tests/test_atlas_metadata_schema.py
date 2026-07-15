from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.dataset_release import RELEASE_DATE, build_staged_release, verify_database
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
    assert len(seed.demo_scenarios) == 5
    assert len(seed.comparison_sets) == 1
    assert len(seed.comparison_set_members) == 3
    assert seed.learning_edges
    assert len(seed.learning_edges) >= 40
    assert len(seed.terminology_aliases) >= 30


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
                  relation_types_json, max_depth, source_ids_json, last_verified,
                  view_id, filter_policy_json, limitations_ja, limitations_en,
                  focus_fallback_entity_types_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    "invalid",
                    '{"mode":"authored_groups","groups":[{"group_id":"x","label_ja":"x","label_en":"x","feature_ids":["F_VARIABLE_DOMAIN"]}]}',
                    "不正",
                    "Invalid",
                    '["feature"]',
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
        learning_count = connection.execute("SELECT COUNT(*) FROM learning_edges").fetchone()[0]
        alias_count = connection.execute("SELECT COUNT(*) FROM terminology_aliases").fetchone()[0]
    finally:
        connection.close()

    assert [row[0] for row in check_rows] == [f"CHK{index:03d}" for index in range(1, 26)]
    assert not [row for row in check_rows if row[1] == "fail"]
    assert {row[2] for row in check_rows} == {RELEASE_DATE}
    assert learning_count >= 40
    assert alias_count >= 30


def test_each_atlas_live_check_detects_its_table_mutation(
    staged_database: Path, tmp_path: Path
) -> None:
    mutations = {
        "CHK014": (
            'UPDATE view_presets SET relation_types_json = \'["x","x"]\' '
            "WHERE preset_id = (SELECT preset_id FROM view_presets LIMIT 1)"
        ),
        "CHK015": (
            "UPDATE method_visualization_profiles "
            'SET state_fields_json = \'["x","x"]\' '
            "WHERE profile_id = (SELECT profile_id FROM method_visualization_profiles LIMIT 1)"
        ),
        "CHK016": (
            "UPDATE demo_scenarios SET budget = 0 "
            "WHERE scenario_id = (SELECT scenario_id FROM demo_scenarios LIMIT 1)"
        ),
        "CHK017": (
            "UPDATE comparison_sets SET synchronization = 'iteration' "
            "WHERE comparison_set_id = (SELECT comparison_set_id FROM comparison_sets LIMIT 1)"
        ),
        "CHK018": (
            "UPDATE learning_edges SET target_id = 'MISSING' "
            "WHERE edge_id = (SELECT edge_id FROM learning_edges LIMIT 1)"
        ),
        "CHK019": (
            "UPDATE method_visualization_profiles SET support_status = '' "
            "WHERE profile_id = (SELECT profile_id FROM method_visualization_profiles LIMIT 1)"
        ),
    }
    for check_id, sql in mutations.items():
        mutated = tmp_path / f"{check_id}.sqlite"
        shutil.copy2(staged_database, mutated)
        connection = sqlite3.connect(mutated)
        try:
            connection.execute("PRAGMA ignore_check_constraints = ON")
            connection.execute(sql)
            connection.commit()
        finally:
            connection.close()

        result = verify_database(mutated)

        assert result.ok is False
        assert check_id in {check.check_id for check in result.live_failures}


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE learning_edges SET relation = 'invalid' WHERE rowid = 1",
        "UPDATE learning_edges SET target_type = source_type, target_id = source_id "
        "WHERE rowid = 1",
        "UPDATE learning_edges SET rationale = ' ' WHERE rowid = 1",
        "UPDATE learning_edges SET display_order = -1 WHERE rowid = 1",
        "INSERT INTO learning_edges SELECT edge_id || '_DUP', source_type, source_id, "
        "target_type, target_id, relation, rationale, difficulty, audience, display_order, "
        "source_ids_json, last_verified, status FROM learning_edges WHERE rowid = 1",
    ],
)
def test_chk018_detects_constraint_bypassed_learning_edge_semantics(
    staged_database: Path, tmp_path: Path, mutation: str
) -> None:
    mutated = tmp_path / "learning-edge.sqlite"
    shutil.copy2(staged_database, mutated)
    connection = sqlite3.connect(mutated)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "CREATE TABLE learning_edges_unconstrained AS SELECT * FROM learning_edges"
        )
        connection.execute("DROP TABLE learning_edges")
        connection.execute("ALTER TABLE learning_edges_unconstrained RENAME TO learning_edges")
        connection.execute(mutation)
        connection.commit()
    finally:
        connection.close()

    result = verify_database(mutated)

    assert result.ok is False
    assert "CHK018" in {check.check_id for check in result.live_failures}


def test_chk025_detects_undisambiguated_alias_collision(
    staged_database: Path, tmp_path: Path
) -> None:
    mutated = tmp_path / "terminology.sqlite"
    shutil.copy2(staged_database, mutated)
    connection = sqlite3.connect(mutated)
    try:
        connection.execute(
            "UPDATE terminology_aliases SET disambiguation_note = NULL "
            "WHERE target_id IN ('MF_DISCRETE_EXACT', 'M_INTERIOR_POINT_NLP')"
        )
        connection.commit()
    finally:
        connection.close()

    result = verify_database(mutated)

    assert result.ok is False
    assert "CHK025" in {check.check_id for check in result.live_failures}
