from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from optimization_compass.content_models import load_content
from optimization_compass.dataset_release import build_staged_release

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"


def test_trf_is_a_canonical_method_with_one_scipy_mapping(tmp_path: Path) -> None:
    staged = build_staged_release(BASE_DATABASE, tmp_path / "release")
    connection = sqlite3.connect(staged.database_path)
    connection.row_factory = sqlite3.Row
    try:
        method = connection.execute(
            "SELECT * FROM methods WHERE method_id = 'M_TRUST_REGION_REFLECTIVE'"
        ).fetchone()
        mappings = connection.execute(
            "SELECT method_id, implementation_id, support_level FROM method_implementation_map "
            "WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF'"
        ).fetchall()
        claim = connection.execute(
            "SELECT value_json, value_status, valid_from, source_id FROM implementation_claims "
            "WHERE subject_id = 'I_SCIPY_LEAST_SQUARES_TRF' "
            "AND predicate = 'important_option_defaults' AND valid_to IS NULL"
        ).fetchone()
    finally:
        connection.close()

    assert method is not None
    assert method["method_family_id"] == "MF_TRUST_REGION"
    assert method["constraint_support"] == "bounds"
    assert method["reference_source_ids"] == "S003;S096"
    assert [tuple(row) for row in mappings] == [
        ("M_TRUST_REGION_REFLECTIVE", "I_SCIPY_LEAST_SQUARES_TRF", "native"),
    ]
    assert claim is not None
    assert claim["value_status"] == "verified"
    assert claim["source_id"] == "S003"
    assert claim["valid_from"] == "2026-07-16"
    default_text = json.loads(claim["value_json"])
    assert "least_squares: method=trf is the default" in default_text
    assert "curve_fit: trf is selected when bounds are supplied" in default_text


def test_trf_has_a_beginner_first_published_guide() -> None:
    pages = {page.content_id: page for page in load_content(ROOT / "content")}
    page = pages["trust-region-reflective"]

    assert page.method_id == "M_TRUST_REGION_REFLECTIVE"
    assert page.status == "published"
    assert page.source_ids == ("S003", "S096")
    assert "この手法の気持ち" in page.body
    assert "## なぜReflectiveなのか" in page.body
    assert "## LM・dogbox・L-BFGS-Bとの違い" in page.body
    assert 'method="trf"' in page.body
