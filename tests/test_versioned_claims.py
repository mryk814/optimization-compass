from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from optimization_compass.dataset_release import build_staged_release, verify_database
from optimization_compass.versioned_claims import (
    HIGH_USAGE_IMPLEMENTATION_IDS,
    claim_freshness_report,
    claims_at,
    comparison_eligibility,
)

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"


@pytest.fixture()
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    staged = build_staged_release(BASE_DATABASE, tmp_path / "release")
    value = sqlite3.connect(staged.database_path)
    value.row_factory = sqlite3.Row
    try:
        yield value
    finally:
        value.close()


def test_every_implementation_has_explicit_active_claims_and_freshness(
    connection: sqlite3.Connection,
) -> None:
    implementation_count = connection.execute("SELECT COUNT(*) FROM implementations").fetchone()[0]
    active_claims = connection.execute(
        "SELECT COUNT(*) FROM implementation_claims WHERE valid_to IS NULL"
    ).fetchone()[0]
    unknowns = connection.execute(
        "SELECT COUNT(*) FROM implementation_claims WHERE value_status = 'explicit_unknown'"
    ).fetchone()[0]

    assert implementation_count == 64
    assert active_claims == implementation_count * 7 + 2
    assert unknowns > 0
    placeholders = ",".join("?" for _ in HIGH_USAGE_IMPLEMENTATION_IDS)
    verified_high_usage = connection.execute(
        f"""
        SELECT COUNT(*) FROM implementation_claims
        WHERE subject_id IN ({placeholders}) AND predicate = 'current_release'
          AND valid_to IS NULL AND value_status = 'verified'
        """,
        tuple(sorted(HIGH_USAGE_IMPLEMENTATION_IDS)),
    ).fetchone()[0]
    assert verified_high_usage / len(HIGH_USAGE_IMPLEMENTATION_IDS) >= 0.8
    freshness = claim_freshness_report(connection, as_of=date(2026, 7, 16))
    assert freshness["claim_count"] == active_claims
    assert len(freshness["claims"]) == active_claims


def test_scipy_trf_defaults_are_separate_versioned_claims(
    connection: sqlite3.Connection,
) -> None:
    rows = connection.execute(
        """
        SELECT claim_id, value_json, value_status, source_id, product_version
        FROM implementation_claims
        WHERE subject_id = 'I_SCIPY_LEAST_SQUARES_TRF'
          AND predicate = 'important_option_defaults'
          AND claim_id LIKE '%DEFAULT_%'
        ORDER BY claim_id
        """
    ).fetchall()

    assert len(rows) == 2
    values = {row["claim_id"]: json.loads(row["value_json"]) for row in rows}
    least_squares = values["CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_LEAST_SQUARES"]
    curve_fit = values["CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_CURVE_FIT_BOUNDS"]

    assert least_squares == {
        "api": "scipy.optimize.least_squares",
        "condition": "method omitted",
        "scope": "nonlinear least squares with or without bounds",
        "selected_method": "trf",
        "user_override": "method",
    }
    assert curve_fit == {
        "api": "scipy.optimize.curve_fit",
        "condition": "bounds provided and method omitted",
        "fallback_without_bounds": "lm",
        "selected_method": "trf",
        "user_override": "method",
    }
    assert all(row["value_status"] == "verified" for row in rows)
    assert all(row["source_id"] == "S003" for row in rows)
    assert all(row["product_version"] for row in rows)


def test_superseded_release_is_reproducible_as_of_date(connection: sqlite3.Connection) -> None:
    old = claims_at(connection, "I_SCIPY_LINPROG_HIGHS", date(2025, 6, 1))
    current = claims_at(connection, "I_SCIPY_LINPROG_HIGHS", date(2026, 7, 16))

    old_release = next(claim for claim in old if claim["predicate"] == "current_release")
    current_release = next(claim for claim in current if claim["predicate"] == "current_release")
    assert old_release["verification_status"] == "superseded"
    assert old_release["replaced_by"] == current_release["claim_id"]
    assert old_release["value_json"] != current_release["value_json"]


def test_comparison_requires_complete_context(connection: sqlite3.Connection) -> None:
    assert comparison_eligibility(None).ranking_eligible is False
    contexts = connection.execute("SELECT * FROM benchmark_contexts ORDER BY category").fetchall()
    assert {row["category"] for row in contexts} == {"LP", "QP", "NLP", "MIP", "DFO", "BO"}
    assert all(comparison_eligibility(dict(row)).ranking_eligible for row in contexts)
    assert (
        connection.execute(
            "SELECT benchmark_context_id FROM comparison_sets WHERE comparison_set_id = ?",
            ("COMPARE_GRADIENT_FAMILY",),
        ).fetchone()[0]
        == "BENCH_QP"
    )
    assert verify_database(
        Path(connection.execute("PRAGMA database_list").fetchone()[2]), require_atlas=True
    ).ok
