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
    ComparisonEligibility,
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
    assert active_claims == implementation_count * 7
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
    freshness = claim_freshness_report(connection, as_of=date(2026, 7, 15))
    assert freshness["claim_count"] == active_claims
    assert len(freshness["claims"]) == active_claims


def test_superseded_release_is_reproducible_as_of_date(connection: sqlite3.Connection) -> None:
    old = claims_at(connection, "I_SCIPY_LINPROG_HIGHS", date(2025, 6, 1))
    current = claims_at(connection, "I_SCIPY_LINPROG_HIGHS", date(2026, 7, 15))

    old_release = next(claim for claim in old if claim["predicate"] == "current_release")
    current_release = next(claim for claim in current if claim["predicate"] == "current_release")
    assert old_release["verification_status"] == "superseded"
    assert old_release["replaced_by"] == current_release["claim_id"]
    assert old_release["value_json"] != current_release["value_json"]


def test_comparison_requires_complete_context(connection: sqlite3.Connection) -> None:
    assert comparison_eligibility(None).ranking_eligible is False
    contexts = connection.execute("SELECT * FROM benchmark_contexts ORDER BY category").fetchall()
    assert {row["category"] for row in contexts} == {"LP", "QP", "NLP", "MIP", "DFO", "BO"}
    educational_bo = next(row for row in contexts if row["context_id"] == "BENCH_BO_EDUCATIONAL_10")
    educational_knapsack = next(
        row for row in contexts if row["context_id"] == "BENCH_KNAPSACK_BNB_EDUCATIONAL_9"
    )
    assert all(
        comparison_eligibility(dict(row)).ranking_eligible
        for row in contexts
        if row["context_id"] not in {"BENCH_BO_EDUCATIONAL_10", "BENCH_KNAPSACK_BNB_EDUCATIONAL_9"}
    )
    assert comparison_eligibility(dict(educational_bo)) == ComparisonEligibility(
        False, "context_forbids_ranking"
    )
    assert educational_bo["problem_instance_id"] == "OBJECTIVE_EDUCATIONAL_WAVY_1D"
    assert educational_bo["evaluation_budget"] == 10
    assert educational_bo["seed_value"] == 2604
    assert json.loads(educational_bo["oracle_budget_json"]) == {
        "limit": 10,
        "unit": "oracle_evaluations",
    }
    assert json.loads(educational_bo["implementation_versions_json"]) == {
        "generator_id": "educational.surrogate_uncertainty.v1",
        "generator_version": "1.0.0",
        "implementation_mapping_status": "not_applicable",
    }
    assert comparison_eligibility(dict(educational_knapsack)) == ComparisonEligibility(
        False, "context_forbids_ranking"
    )
    assert educational_knapsack["problem_instance_id"] == "INSTANCE_BINARY_KNAPSACK_4"
    assert educational_knapsack["evaluation_budget"] == 9
    assert educational_knapsack["seed_value"] == 0
    assert json.loads(educational_knapsack["oracle_budget_json"]) == {
        "limit": 9,
        "unit": "oracle_evaluations",
    }
    assert json.loads(educational_knapsack["stopping_json"]) == {
        "member_values": [4, 9],
        "policy": "member_node_stop_limit",
    }
    assert json.loads(educational_knapsack["implementation_versions_json"]) == {
        "generator_id": "educational.branch_bound.knapsack.v1",
        "generator_version": "1.1.0",
        "implementation_mapping_status": "not_applicable",
    }
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
