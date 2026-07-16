from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any

CLAIM_PREDICATES: tuple[tuple[str, str], ...] = (
    ("current_release", "last_release"),
    ("maintenance_status", "maintenance_status"),
    ("license_spdx", "license"),
    ("platform_architecture", "os_support"),
    ("gpu_distributed_support", "gpu_support"),
    ("supported_problem_classes", "supported_method_ids"),
    ("important_option_defaults", "major_options"),
)

# High usage means currently exposed by the published Gallery or selected implicitly by a common API.
HIGH_USAGE_IMPLEMENTATION_IDS = frozenset(
    {"I_ORTOOLS_CPSAT", "I_OPTUNA", "I_CVXPY", "I_SCIPY_LEAST_SQUARES_TRF"}
)


@dataclass(frozen=True)
class ComparisonEligibility:
    ranking_eligible: bool
    reason: str


def comparison_eligibility(context: dict[str, Any] | None) -> ComparisonEligibility:
    if context is None:
        return ComparisonEligibility(False, "benchmark_context_required")
    required = (
        "problem_instance_id",
        "dimension",
        "hardware_json",
        "runtime_json",
        "oracle_budget_json",
        "evaluation_budget",
        "tolerance_json",
        "stopping_json",
        "initialization_json",
        "tuning_policy",
        "implementation_versions_json",
        "outcome_metrics_json",
        "status_mapping_json",
    )
    missing = [field for field in required if context.get(field) in (None, "", "{}", "[]")]
    if missing:
        return ComparisonEligibility(False, "missing_context:" + ",".join(missing))
    return ComparisonEligibility(True, "context_complete")


def insert_versioned_claims_and_contexts(
    connection: sqlite3.Connection, *, release_date: str
) -> None:
    connection.execute(
        """
        UPDATE implementations
        SET last_release = '9.15 (2026-01-12)', last_verified = ?
        WHERE implementation_id IN (
          'I_ORTOOLS_CPSAT', 'I_ORTOOLS_GLOP', 'I_ORTOOLS_PDLP', 'I_ORTOOLS_ROUTING'
        )
        """,
        (release_date,),
    )
    implementations = connection.execute(
        "SELECT * FROM implementations ORDER BY implementation_id"
    ).fetchall()
    source_dates = {
        str(row["source_id"]): row["publication_date"]
        for row in connection.execute("SELECT source_id, publication_date FROM sources")
    }
    for implementation in implementations:
        source_id = _first_source_id(str(implementation["source_ids"] or ""))
        if source_id is None:
            raise ValueError(f"implementation has no source: {implementation['implementation_id']}")
        subject_id = str(implementation["implementation_id"])
        last_verified = str(implementation["last_verified"] or release_date)
        for predicate, column in CLAIM_PREDICATES:
            raw_value = implementation[column]
            known = raw_value is not None and str(raw_value).strip().lower() not in {"", "unknown"}
            claim_id = f"CLAIM_{subject_id.removeprefix('I_')}_{predicate.upper()}"
            value: object = str(raw_value) if known else {"status": "unknown"}
            connection.execute(
                """
                INSERT INTO implementation_claims (
                  claim_id, subject_id, predicate, value_json, value_status, valid_from,
                  valid_to, replaced_by, source_id, source_date, last_verified, confidence,
                  verification_status, product_version, commit_sha, release_tag
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    claim_id,
                    subject_id,
                    predicate,
                    _json(value),
                    "verified" if known else "explicit_unknown",
                    last_verified,
                    source_id,
                    source_dates[source_id] or last_verified,
                    last_verified,
                    str(implementation["confidence"] or "unverified"),
                    "verified" if known else "source_pending",
                    str(raw_value) if known and predicate == "current_release" else None,
                    str(raw_value) if known and predicate == "current_release" else None,
                ),
            )

    _insert_scipy_default_claims(connection, release_date)
    _insert_historical_release_fixture(connection)
    for context in _benchmark_context_fixtures(connection, release_date):
        columns = list(context)
        connection.execute(
            f"INSERT INTO benchmark_contexts ({', '.join(columns)}) "
            f"VALUES ({', '.join('?' for _ in columns)})",
            [context[column] for column in columns],
        )
    connection.execute(
        "UPDATE comparison_sets SET benchmark_context_id = 'BENCH_QP' "
        "WHERE comparison_set_id = 'COMPARE_GRADIENT_FAMILY'"
    )


def claims_at(connection: sqlite3.Connection, subject_id: str, as_of: date) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT * FROM implementation_claims
        WHERE subject_id = ? AND valid_from <= ?
          AND (valid_to IS NULL OR valid_to >= ?)
        ORDER BY predicate, claim_id
        """,
        (subject_id, as_of.isoformat(), as_of.isoformat()),
    ).fetchall()
    return [dict(row) for row in rows]


def claim_freshness_report(connection: sqlite3.Connection, *, as_of: date) -> dict[str, Any]:
    rows = connection.execute(
        "SELECT claim_id, subject_id, predicate, value_status, last_verified "
        "FROM implementation_claims WHERE valid_to IS NULL ORDER BY claim_id"
    ).fetchall()
    claims = []
    for row in rows:
        age_days = (as_of - date.fromisoformat(str(row["last_verified"]))).days
        claims.append(
            {
                **dict(row),
                "age_days": age_days,
                "freshness_status": "current" if age_days <= 180 else "stale",
            }
        )
    return {
        "as_of": as_of.isoformat(),
        "claim_count": len(claims),
        "explicit_unknown_count": sum(
            item["value_status"] == "explicit_unknown" for item in claims
        ),
        "claims": claims,
    }


def _insert_scipy_default_claims(connection: sqlite3.Connection, release_date: str) -> None:
    implementation = connection.execute(
        """
        SELECT last_release, confidence
        FROM implementations
        WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF'
        """
    ).fetchone()
    if implementation is None:
        raise ValueError("SciPy TRF implementation fixture is missing")
    product_version = str(implementation["last_release"] or "unknown")
    confidence = str(implementation["confidence"] or "unverified")
    claims = (
        (
            "CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_LEAST_SQUARES",
            {
                "api": "scipy.optimize.least_squares",
                "condition": "method omitted",
                "selected_method": "trf",
                "scope": "nonlinear least squares with or without bounds",
                "user_override": "method",
            },
        ),
        (
            "CLAIM_SCIPY_LEAST_SQUARES_TRF_DEFAULT_CURVE_FIT_BOUNDS",
            {
                "api": "scipy.optimize.curve_fit",
                "condition": "bounds provided and method omitted",
                "selected_method": "trf",
                "fallback_without_bounds": "lm",
                "user_override": "method",
            },
        ),
    )
    for claim_id, value in claims:
        connection.execute(
            """
            INSERT INTO implementation_claims (
              claim_id, subject_id, predicate, value_json, value_status, valid_from,
              valid_to, replaced_by, source_id, source_date, last_verified, confidence,
              verification_status, product_version, commit_sha, release_tag
            ) VALUES (
              ?, 'I_SCIPY_LEAST_SQUARES_TRF', 'important_option_defaults', ?, 'verified', ?,
              NULL, NULL, 'S003', ?, ?, ?, 'verified', ?, NULL, NULL
            )
            """,
            (
                claim_id,
                _json(value),
                release_date,
                release_date,
                release_date,
                confidence,
                product_version,
            ),
        )


def _insert_historical_release_fixture(connection: sqlite3.Connection) -> None:
    current = connection.execute(
        """
        SELECT claim_id, source_id, source_date, last_verified, confidence
        FROM implementation_claims
        WHERE subject_id = 'I_SCIPY_LINPROG_HIGHS' AND predicate = 'current_release'
        """
    ).fetchone()
    if current is None:
        raise ValueError("SciPy release claim fixture is missing")
    connection.execute(
        "UPDATE implementation_claims SET valid_from = '2026-01-01' WHERE claim_id = ?",
        (current["claim_id"],),
    )
    connection.execute(
        """
        INSERT INTO implementation_claims (
          claim_id, subject_id, predicate, value_json, value_status, valid_from, valid_to,
          replaced_by, source_id, source_date, last_verified, confidence,
          verification_status, product_version, commit_sha, release_tag
        ) VALUES (
          'CLAIM_SCIPY_LINPROG_HIGHS_CURRENT_RELEASE_2025', 'I_SCIPY_LINPROG_HIGHS',
          'current_release', '"SciPy 1.15.x"', 'verified', '2025-01-01', '2025-12-31',
          ?, ?, ?, '2025-01-01', ?, 'superseded', 'SciPy 1.15.x', NULL, 'v1.15'
        )
        """,
        (current["claim_id"], current["source_id"], current["source_date"], current["confidence"]),
    )


def _benchmark_context_fixtures(
    connection: sqlite3.Connection, release_date: str
) -> list[dict[str, object]]:
    fixtures = (
        ("LP", "INSTANCE_ASSIGNMENT_3X3", 9, "I_HIGHS_NATIVE", 100),
        ("QP", "OBJECTIVE_QUADRATIC_2D", 2, "I_OSQP", 40),
        ("NLP", "OBJECTIVE_ROSENBROCK_2D", 2, "I_IPOPT", 200),
        ("MIP", "INSTANCE_BINARY_KNAPSACK_4", 4, "I_SCIP", 100),
        ("DFO", "INSTANCE_RASTRIGIN_2D", 2, "I_NLOPT", 300),
        ("BO", "OBJECTIVE_EDUCATIONAL_WAVY_1D", 1, "I_BOTORCH", 25),
    )
    results: list[dict[str, object]] = []
    for category, instance_id, dimension, implementation_id, budget in fixtures:
        instance = connection.execute(
            "SELECT source_ids_json FROM problem_instances WHERE problem_instance_id = ?",
            (instance_id,),
        ).fetchone()
        implementation = connection.execute(
            "SELECT last_release FROM implementations WHERE implementation_id = ?",
            (implementation_id,),
        ).fetchone()
        if instance is None or implementation is None:
            raise ValueError(f"benchmark fixture does not resolve: {category}")
        results.append(
            {
                "context_id": f"BENCH_{category}",
                "context_version": "1.0.0",
                "category": category,
                "problem_instance_id": instance_id,
                "problem_variant": "canonical educational instance; no hidden preprocessing",
                "dimension": dimension,
                "sparsity_json": _json({"status": "reported", "structure": "instance-defined"}),
                "hardware_json": _json({"cpu": "reference-cpu", "threads": 1}),
                "runtime_json": _json({"os": "platform-neutral", "precision": "float64"}),
                "oracle_budget_json": _json({"unit": "objective_evaluations", "limit": budget}),
                "evaluation_budget": budget,
                "time_budget_seconds": 60.0,
                "tolerance_json": _json({"absolute": 1e-6, "relative": 1e-6}),
                "stopping_json": _json({"budget_or_tolerance": "first_reached"}),
                "initialization_json": _json({"policy": "canonical_instance_candidates"}),
                "seed_status": "fixed" if category in {"DFO", "BO"} else "not_applicable",
                "seed_value": 42 if category in {"DFO", "BO"} else None,
                "tuning_policy": "documented defaults; no per-instance winner tuning",
                "implementation_versions_json": _json(
                    {implementation_id: str(implementation["last_release"] or "unknown")}
                ),
                "outcome_metrics_json": _json(
                    ["status", "objective_value", "constraint_violation", "evaluation_count"]
                ),
                "status_mapping_json": _json(
                    {"success": "eligible", "budget_exhausted": "incomplete", "error": "failed"}
                ),
                "source_ids_json": str(instance["source_ids_json"]),
                "last_verified": release_date,
            }
        )
    return results


def _first_source_id(value: str) -> str | None:
    return next((item.strip() for item in value.split(";") if item.strip()), None)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
