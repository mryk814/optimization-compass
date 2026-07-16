from __future__ import annotations

import sqlite3
from pathlib import Path

from optimization_compass.dataset_release import build_staged_release, verify_database

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"


def test_trust_region_reflective_has_one_canonical_method_and_scipy_mapping(
    tmp_path: Path,
) -> None:
    staged = build_staged_release(BASE_DATABASE, tmp_path / "release")
    connection = sqlite3.connect(staged.database_path)
    connection.row_factory = sqlite3.Row
    try:
        method = connection.execute(
            "SELECT * FROM methods WHERE method_id = 'M_TRUST_REGION_REFLECTIVE'"
        ).fetchone()
        mappings = connection.execute(
            """
            SELECT method_id, support_level, method_selector
            FROM method_implementation_map
            WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF'
            """
        ).fetchall()
        implementation = connection.execute(
            """
            SELECT supported_method_ids, method_selector, source_ids
            FROM implementations
            WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF'
            """
        ).fetchone()
        hierarchy = connection.execute(
            """
            SELECT parent_method_id, relation_type
            FROM method_hierarchy
            WHERE child_method_id = 'M_TRUST_REGION_REFLECTIVE'
            """
        ).fetchone()
        source = connection.execute(
            "SELECT source_type, title FROM sources WHERE source_id = 'S096'"
        ).fetchone()
        method_count = connection.execute("SELECT COUNT(*) FROM methods").fetchone()[0]
    finally:
        connection.close()

    assert staged.version == "0.11.0"
    assert method_count == 99
    assert method is not None
    assert method["method_family_id"] == "M_TRUST_REGION"
    assert method["constraint_support"] == "bounds"
    assert method["reference_source_ids"] == "S003;S096"
    assert [tuple(row) for row in mappings] == [
        ("M_TRUST_REGION_REFLECTIVE", "native", "trf")
    ]
    assert implementation is not None
    assert implementation["supported_method_ids"] == "M_TRUST_REGION_REFLECTIVE"
    assert implementation["method_selector"] == "trf"
    assert implementation["source_ids"] == "S003;S096;S082"
    assert hierarchy is not None
    assert tuple(hierarchy) == ("M_TRUST_REGION", "variant_of")
    assert source is not None
    assert source["source_type"] == "original_paper"
    assert "Bound-Constrained" in source["title"]
    assert verify_database(staged.database_path, require_atlas=True).ok
